import { Component, ElementRef, ViewChild, effect, signal } from '@angular/core';
import { JsonPipe } from '@angular/common';
import {
  ConversationApi,
  ConversationNotFoundError,
  MessageChunkEvent,
  MessageRole,
} from '../conversation-api/conversation-api';

export type MessageStatus = 'pending' | 'processed' | 'failed';

export interface MessageVm {
  id: string;
  role: MessageRole;
  status: MessageStatus;
  content: string;
}

const STORAGE_KEY = 'conversation_id';

@Component({
  selector: 'app-conversation-page',
  imports: [JsonPipe],
  templateUrl: './conversation-page.html',
  styleUrl: './conversation-page.scss',
})
export class ConversationPage {
  protected readonly conversationId = signal<string | null>(null);
  protected readonly messages = signal<MessageVm[]>([]);
  protected readonly eventData = signal<unknown>(null);
  protected readonly eventError = signal<string | null>(null);
  protected readonly loadError = signal<string | null>(null);
  protected readonly sending = signal(false);
  protected readonly initializing = signal(true);

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLElement>;
  @ViewChild('draftInput') private draftInput?: ElementRef<HTMLTextAreaElement>;

  constructor(private readonly api: ConversationApi) {
    effect(() => {
      this.messages();
      queueMicrotask(() => this.scrollAnchor?.nativeElement.scrollIntoView({ block: 'end' }));
    });
    void this.init();
  }

  private async init(): Promise<void> {
    this.initializing.set(true);
    this.loadError.set(null);
    try {
      let id = localStorage.getItem(STORAGE_KEY);
      if (!id) {
        id = await this.api.createConversation();
        localStorage.setItem(STORAGE_KEY, id);
      }
      this.conversationId.set(id);
      await this.loadFrom(id, null);
    } catch (error) {
      if (error instanceof ConversationNotFoundError) {
        localStorage.removeItem(STORAGE_KEY);
        return this.init();
      }
      this.loadError.set(describeError(error));
      return;
    } finally {
      this.initializing.set(false);
    }
    await this.refreshEvent();
  }

  protected async send(): Promise<void> {
    const textarea = this.draftInput?.nativeElement;
    const content = textarea?.value.trim();
    const id = this.conversationId();
    if (!content || !id || this.sending()) return;

    this.sending.set(true);
    this.loadError.set(null);
    const lastId = this.messages().at(-1)?.id ?? null;
    if (textarea) textarea.value = '';

    try {
      await this.api.postMessage(id, content);
      await this.loadFrom(id, lastId);
    } catch (error) {
      this.loadError.set(describeError(error));
    } finally {
      this.sending.set(false);
    }
    await this.refreshEvent();
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void this.send();
    }
  }

  private async loadFrom(conversationId: string, startMessageId: string | null): Promise<void> {
    const touched = new Map<string, 'ok' | 'error'>();

    await this.api.streamMessages(conversationId, startMessageId, (eventName, data) => {
      const outcome = eventName === 'error' ? 'error' : 'ok';
      touched.set(data.message_id, outcome);
      this.applyChunk(data, outcome);
    });

    for (const [messageId, outcome] of touched) {
      if (outcome === 'ok') this.finalize(messageId, 'processed');
    }
  }

  private applyChunk(data: MessageChunkEvent, outcome: 'ok' | 'error'): void {
    this.messages.update((current) => {
      const index = current.findIndex((m) => m.id === data.message_id);
      if (index === -1) {
        const created: MessageVm = {
          id: data.message_id,
          role: data.role,
          status: outcome === 'error' ? 'failed' : 'pending',
          content: data.content ?? '',
        };
        return [...current, created];
      }
      const existing = current[index];
      const updated: MessageVm = {
        ...existing,
        status: outcome === 'error' ? 'failed' : existing.status,
        content: outcome === 'error' ? existing.content : existing.content + (data.content ?? ''),
      };
      return current.map((m, i) => (i === index ? updated : m));
    });
  }

  private finalize(messageId: string, status: MessageStatus): void {
    this.messages.update((current) =>
      current.map((m) => (m.id === messageId && m.status === 'pending' ? { ...m, status } : m)),
    );
  }

  private async refreshEvent(): Promise<void> {
    const id = this.conversationId();
    if (!id) return;
    try {
      const data = await this.api.getEvent(id);
      this.eventData.set(data);
      this.eventError.set(null);
    } catch (error) {
      this.eventError.set(describeError(error));
    }
  }
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong';
}
