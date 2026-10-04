import { Component, effect, inject, input, signal, untracked } from '@angular/core';
import { ComposerComponent } from '../../components/composer/composer-component';
import { ComposerVM } from '../../components/composer/composer-vm';
import { EventComponent } from '../../components/event/event-component';
import { EventVM } from '../../components/event/event-vm';
import { MessagesComponent } from '../../components/messages/messages-component';
import { MessageStatus, MessagesVM, MessageVM } from '../../components/messages/messages-vm';
import {
  ActivityChunk,
  AgentService,
  ErrorChunk,
  MessageChunk,
  MessageRole,
} from '../../services/agent-service';
import { describeError, isAbortError } from '../../utils/error-utils';
import {
  append,
  findBy,
  patch,
  updateBy,
  updateField,
  updateWhere,
  upsertBy,
} from '../../utils/signal-utils';

@Component({
  selector: 'app-conversation-page',
  imports: [MessagesComponent, ComposerComponent, EventComponent],
  templateUrl: './conversation-page.html',
  host: {
    class: 'flex h-dvh w-full flex-col bg-slate-50 md:flex-row',
  },
})
export class ConversationPage {
  private readonly agent = inject(AgentService);

  readonly id = input.required<string>();

  private loadMessagesController: AbortController | null = null;
  private postMessageController: AbortController | null = null;
  private loadMessagesFromController: AbortController | null = null;
  private loadEventController: AbortController | null = null;

  protected readonly messages = signal<MessagesVM>({ status: 'loading', error: null, items: [] });
  protected readonly composer = signal<ComposerVM>({ status: 'disabled', draft: '', error: null });
  protected readonly event = signal<EventVM>({ status: 'loading', data: null, error: null });

  constructor() {
    // Entry point：
    // 监听 1 个东西，变化就从头加载整个会话：
    //   - 输入 id
    // 先加载全部消息，成功后再加载 event
    effect((onCleanup) => {
      const id = this.id();
      untracked(async () => {
        if (await this.loadMessages(id)) await this.loadEvent(id);
      });

      // Entry point：
      // id 变化或页面销毁时，取消所有进行中的请求：
      // abort 4 个控制器，旧请求直接进 catch，不会再写入状态
      onCleanup(() => {
        this.loadMessagesController?.abort();
        this.postMessageController?.abort();
        this.loadMessagesFromController?.abort();
        this.loadEventController?.abort();
      });
    });
  }

  // Entry point：
  // 用户点 Retry 时，重新加载消息：
  //   - messageId：null = 整体重试，否则 = 从该消息起重试
  // 忙着时不响应；加载消息没被取代，就再加载 event
  protected async onRetry(messageId: string | null): Promise<void> {
    const status = this.messages().status;
    if (status !== 'ready' && status !== 'failed') return;
    if (this.composer().status === 'submitting') return;

    const conversationId = this.id();
    const loaded =
      messageId === null
        ? await this.loadMessages(conversationId)
        : await this.loadMessagesFrom(conversationId, messageId);
    if (loaded) await this.loadEvent(conversationId);
  }

  // Entry point：
  // 用户发送消息时，先发送，再加载消息：
  //   - content：草稿内容
  // 发送成功后从这条消息起加载消息；没被取代，就再加载 event
  protected async onSubmit(content: string): Promise<void> {
    if (this.composer().status !== 'ready') return;

    const conversationId = this.id();
    const messageId = await this.postMessage(conversationId, content);
    if (!messageId) return;
    if (await this.loadMessagesFrom(conversationId, messageId))
      await this.loadEvent(conversationId);
  }

  // Entry point：
  // 用户点 AI 消息改动记录的折叠条时，展开或收起它：
  //   - messageId：被点的消息
  // 没有任何前置检查，消息在 streaming 或 failed 时也照常响应
  protected onToggleActivity(messageId: string): void {
    this.toggleActivity(messageId);
  }

  // Workflow：加载全部消息
  // 返回：是否加载成功
  //   - conversationId：要加载的会话
  // 开始：Messages：删（清空 items）+ 改（status: loading, error: null）；Composer：改（status: disabled）
  // 成功：Messages：增/改（applyMessageChunk 追加或接上 items、applyActivityChunk 追加 items 的 activity）+ 改（applyErrorChunk 把 items 标成 failed）+ 改（status: ready, error: null）；Composer：改（status: ready）
  // 失败：Messages：改（status: failed, error）
  // 收尾：Messages：改（streaming 的 items 改成 done）
  private async loadMessages(conversationId: string): Promise<boolean> {
    this.loadMessagesController?.abort();
    this.loadMessagesController = new AbortController();
    const { signal } = this.loadMessagesController;

    this.messages.set({ status: 'loading', error: null, items: [] });
    patch(this.composer, { status: 'disabled' });

    try {
      await this.agent.streamMessages(conversationId, null, this.streamHandlers, signal);
      patch(this.messages, { status: 'ready', error: null });
      patch(this.composer, { status: 'ready' });
      return true;
    } catch (error) {
      if (isAbortError(error)) return false;
      patch(this.messages, { status: 'failed', error: describeError(error) });
      return false;
    } finally {
      if (!signal.aborted) {
        updateField(this.messages, 'items', (items) =>
          updateWhere(
            items,
            (message) => message.status === 'streaming',
            (message) => ({ ...message, status: 'done' }),
          ),
        );
      }
    }
  }

  // Workflow：发消息
  // 返回：成功返回新消息 id，失败返回 null
  //   - conversationId：目标会话
  //   - content：消息内容
  // 开始：Composer：改（status: submitting）
  // 成功：Messages：增（追加占位消息）；Composer：改（清空 draft）
  // 失败：Composer：改（status: ready, error）
  private async postMessage(conversationId: string, content: string): Promise<string | null> {
    this.postMessageController?.abort();
    this.postMessageController = new AbortController();
    const { signal } = this.postMessageController;

    patch(this.composer, { status: 'submitting' });

    try {
      const messageId = await this.agent.postMessage(conversationId, content, signal);
      updateField(this.messages, 'items', (items) =>
        append(items, { id: messageId, role: 'user', status: 'streaming', content: '' }),
      );
      this.composer.update((composer) =>
        composer.draft.trim() === content ? { ...composer, draft: '' } : composer,
      );
      return messageId;
    } catch (error) {
      if (isAbortError(error)) return null;
      patch(this.composer, { status: 'ready', error: describeError(error) });
      return null;
    }
  }

  // Workflow：从某条消息起加载消息（包括这条）
  // 返回：是否执行完成（没被取代），不代表加载成功
  //   - conversationId：目标会话
  //   - messageId：起点消息
  // 开始：Composer：改（status: submitting）；Messages：改（清空起点消息内容, status: streaming）+ 删（起点之后的消息）
  // 成功：Messages：增/改（applyMessageChunk 追加或接上 items、applyActivityChunk 追加 items 的 activity）+ 改（applyErrorChunk 把 items 标成 failed）；Composer：改（status: ready）
  // 失败：Messages：改（起点消息 status: failed）；Composer：改（status: disabled）
  // 收尾：Messages：改（起点及之后、streaming 的 items 改成 done）
  private async loadMessagesFrom(conversationId: string, messageId: string): Promise<boolean> {
    this.loadMessagesFromController?.abort();
    this.loadMessagesFromController = new AbortController();
    const { signal } = this.loadMessagesFromController;

    patch(this.composer, { status: 'submitting' });
    updateField(this.messages, 'items', (items) => {
      const index = items.findIndex((message) => message.id === messageId);
      if (index < 0) return items;
      return [
        ...items.slice(0, index),
        { ...items[index], status: 'streaming' as MessageStatus, content: '' },
      ];
    });

    try {
      await this.agent.streamMessages(conversationId, messageId, this.streamHandlers, signal);
      patch(this.composer, { status: 'ready' });
    } catch (error) {
      if (isAbortError(error)) return false;
      updateField(this.messages, 'items', (items) =>
        updateBy(items, 'id', messageId, (message) => ({ ...message, status: 'failed' })),
      );
      patch(this.composer, { status: 'disabled' });
    } finally {
      if (!signal.aborted) {
        updateField(this.messages, 'items', (items) => {
          const from = items.findIndex((message) => message.id === messageId);
          return updateWhere(
            items,
            (message, index) => index >= from && message.status === 'streaming',
            (message) => ({ ...message, status: 'done' }),
          );
        });
      }
    }

    return true;
  }

  // Workflow：加载侧边栏 event
  // 返回：无
  //   - conversationId：目标会话
  // 开始：Event：改（status: loading, data: null）
  // 成功：Event：改（status: loaded, data）
  // 失败：Event：改（status: failed, error）
  private async loadEvent(conversationId: string): Promise<void> {
    this.loadEventController?.abort();
    this.loadEventController = new AbortController();
    const { signal } = this.loadEventController;

    this.event.set({ status: 'loading', data: null, error: null });

    try {
      const data = await this.agent.getEvent(conversationId, signal);
      this.event.set({ status: 'loaded', data, error: null });
    } catch (error) {
      if (isAbortError(error)) return;
      this.event.set({ status: 'failed', data: null, error: describeError(error) });
    }
  }

  // Workflow：展开或收起一条 AI 消息的改动记录（不调 API）
  // 返回：无
  //   - messageId：要翻转的消息
  // 成功：Messages：改（这条消息的 expanded 取反）
  private toggleActivity(messageId: string): void {
    updateField(this.messages, 'items', (items) =>
      updateBy(items, 'id', messageId, (message) =>
        message.role === 'assistant' ? { ...message, expanded: !message.expanded } : message,
      ),
    );
  }

  // Callback：每遇到还没有的消息 id，生成一条空的 MessageVM：user 只有正文字段，assistant 另带空 activity、expanded: false
  private createMessage(id: string, role: MessageRole): MessageVM {
    return role === 'user'
      ? { id, role, status: 'streaming', content: '' }
      : { id, role, status: 'streaming', content: '', activity: [], expanded: false };
  }

  // Callback：每收到一个 MessageChunk，改一次 MessagesVM 的 items：按 id 找到这条消息，把 chunk 内容接在后面，其余字段保留；找不到就追加一条新的
  private applyMessageChunk = (chunk: MessageChunk): void => {
    updateField(this.messages, 'items', (items) => {
      const previous =
        findBy(items, 'id', chunk.message_id) ?? this.createMessage(chunk.message_id, chunk.role);
      return upsertBy(items, 'id', {
        ...previous,
        status: 'streaming',
        content: previous.content + chunk.content,
      });
    });
  };

  // Callback：每收到一个 ActivityChunk，改一次 MessagesVM 的 items：按 id 找到这条 AI 消息，把 chunk 的 items 接在 activity 后面，其余字段保留；找不到就追加一条新的
  private applyActivityChunk = (chunk: ActivityChunk): void => {
    updateField(this.messages, 'items', (items) => {
      const previous =
        findBy(items, 'id', chunk.message_id) ?? this.createMessage(chunk.message_id, chunk.role);
      if (previous.role !== 'assistant') return items;
      return upsertBy(items, 'id', {
        ...previous,
        status: 'streaming',
        activity: append(previous.activity, ...chunk.items),
      });
    });
  };

  // Callback：每收到一个 ErrorChunk，改一次 MessagesVM 的 items：按 id 找到这条消息，状态记为 failed，其余字段保留；找不到就追加一条空内容的
  private applyErrorChunk = (chunk: ErrorChunk): void => {
    updateField(this.messages, 'items', (items) => {
      const previous =
        findBy(items, 'id', chunk.message_id) ?? this.createMessage(chunk.message_id, chunk.role);
      return upsertBy(items, 'id', { ...previous, status: 'failed' });
    });
  };

  private readonly streamHandlers = {
    onMessageChunk: this.applyMessageChunk,
    onActivityChunk: this.applyActivityChunk,
    onErrorChunk: this.applyErrorChunk,
  };
}
