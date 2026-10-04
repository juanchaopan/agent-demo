import { Injectable } from '@angular/core';
import { ActivityItem } from '../components/activity/activity-vm';
import { readSse } from '../utils/sse-utils';

export type MessageRole = 'user' | 'assistant';

export interface MessageChunk {
  message_id: string;
  role: MessageRole;
  content: string;
}

export interface ActivityChunk {
  message_id: string;
  role: MessageRole;
  items: ActivityItem[];
}

export interface ErrorChunk {
  message_id: string;
  role: MessageRole;
}

export interface MessageStreamHandlers {
  onMessageChunk: (chunk: MessageChunk) => void;
  onActivityChunk: (chunk: ActivityChunk) => void;
  onErrorChunk: (chunk: ErrorChunk) => void;
}

const API_BASE = 'api';

@Injectable({ providedIn: 'root' })
export class AgentService {
  async createConversation(signal?: AbortSignal): Promise<string> {
    const res = await this.request('create conversation', '/conversations', {
      method: 'POST',
      signal,
    });
    const { conversation_id } = (await res.json()) as { conversation_id: string };
    return conversation_id;
  }

  async postMessage(
    conversationId: string,
    content: string,
    signal?: AbortSignal,
  ): Promise<string> {
    const res = await this.request('send message', `/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: content,
      signal,
    });
    const { message_id } = (await res.json()) as { message_id: string };
    return message_id;
  }

  async getEvent(conversationId: string, signal?: AbortSignal): Promise<unknown> {
    const res = await this.request('load event', `/conversations/${conversationId}/event`, {
      signal,
    });
    return res.json();
  }

  /**
   * Reads the message feed from `fromMessageId` (the full history when null) until the server
   * ends the response. `message` frames go to `onMessageChunk`, `activity` frames to
   * `onActivityChunk`, `error` frames to `onErrorChunk`.
   */
  async streamMessages(
    conversationId: string,
    fromMessageId: string | null,
    { onMessageChunk, onActivityChunk, onErrorChunk }: MessageStreamHandlers,
    signal?: AbortSignal,
  ): Promise<void> {
    const query = fromMessageId ? `?start_message_id=${encodeURIComponent(fromMessageId)}` : '';
    const res = await this.request(
      'open message stream',
      `/conversations/${conversationId}/messages${query}`,
      { headers: { Accept: 'text/event-stream' }, signal },
    );

    for await (const { event, data } of readSse(res)) {
      if (event === 'activity') onActivityChunk(JSON.parse(data) as ActivityChunk);
      else if (event === 'error') onErrorChunk(JSON.parse(data) as ErrorChunk);
      else onMessageChunk(JSON.parse(data) as MessageChunk);
    }
  }

  private async request(action: string, path: string, init?: RequestInit): Promise<Response> {
    const res = await fetch(`${API_BASE}${path}`, init);
    if (!res.ok) throw new Error(`Failed to ${action} (${res.status})`);
    return res;
  }
}
