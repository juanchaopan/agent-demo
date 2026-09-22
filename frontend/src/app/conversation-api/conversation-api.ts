import { Injectable } from '@angular/core';

export type MessageRole = 'user' | 'assistant';

export interface MessageChunkEvent {
  message_id: string;
  role: MessageRole;
  content?: string;
}

type SseHandler = (eventName: string, data: MessageChunkEvent) => void;

const API_BASE = 'api';

/** Parses one `\n\n`-delimited SSE frame into (event name, JSON payload). */
function parseSseFrame(frame: string): { eventName: string; data: unknown } | null {
  let eventName = 'message';
  const dataLines: string[] = [];
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice('event:'.length).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trim());
    }
  }
  if (dataLines.length === 0) return null;
  try {
    return { eventName, data: JSON.parse(dataLines.join('\n')) };
  } catch {
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class ConversationApi {
  async createConversation(): Promise<string> {
    const res = await fetch(`${API_BASE}/conversations`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to create conversation (${res.status})`);
    const body = (await res.json()) as { conversation_id: string };
    return body.conversation_id;
  }

  async postMessage(conversationId: string, content: string): Promise<string> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: content,
    });
    if (res.status === 404) throw new ConversationNotFoundError();
    if (!res.ok) throw new Error(`Failed to send message (${res.status})`);
    const body = (await res.json()) as { message_id: string };
    return body.message_id;
  }

  async getEvent(conversationId: string): Promise<unknown> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/event`);
    if (res.status === 404) throw new ConversationNotFoundError();
    if (!res.ok) throw new Error(`Failed to load event (${res.status})`);
    return res.json();
  }

  /**
   * Reads the SSE message feed from `startMessageId` (or the full history when
   * omitted) until the server ends the response, dispatching each frame to `onEvent`.
   */
  async streamMessages(
    conversationId: string,
    startMessageId: string | null,
    onEvent: SseHandler,
    signal?: AbortSignal,
  ): Promise<void> {
    const url = new URL(`${API_BASE}/conversations/${conversationId}/messages`, window.location.href);
    if (startMessageId) url.searchParams.set('start_message_id', startMessageId);

    const res = await fetch(url, { headers: { Accept: 'text/event-stream' }, signal });
    if (res.status === 404) throw new ConversationNotFoundError();
    if (!res.ok || !res.body) throw new Error(`Failed to open message stream (${res.status})`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sepIndex: number;
      while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const parsed = parseSseFrame(frame);
        if (parsed) onEvent(parsed.eventName, parsed.data as MessageChunkEvent);
      }
    }
  }
}

export class ConversationNotFoundError extends Error {
  constructor() {
    super('Conversation not found');
  }
}
