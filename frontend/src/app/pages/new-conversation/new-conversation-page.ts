import { Component, effect, inject, signal, untracked } from '@angular/core';
import { Router } from '@angular/router';
import { NoticeComponent } from '../../components/notice/notice-component';
import { NoticeVM } from '../../components/notice/notice-vm';
import { AgentService } from '../../services/agent-service';
import { describeError, isAbortError } from '../../utils/error-utils';

@Component({
  selector: 'app-new-conversation-page',
  imports: [NoticeComponent],
  templateUrl: './new-conversation-page.html',
})
export class NewConversationPage {
  private readonly agent = inject(AgentService);
  private readonly router = inject(Router);

  private createConversationController: AbortController | null = null;

  protected readonly notice = signal<NoticeVM>({
    status: 'loading',
    text: 'Creating conversation…',
  });

  constructor() {
    // Entry point：
    // 不监听任何东西，页面创建时执行一次：创建会话并跳转
    effect((onCleanup) => {
      untracked(() => void this.createConversation());

      // Entry point：
      // 页面销毁时，取消进行中的请求：
      // abort createConversationController，中断还在进行的创建会话请求
      onCleanup(() => this.createConversationController?.abort());
    });
  }

  // Workflow：创建会话，成功后跳到该会话
  // 返回：无
  // 开始：Notice：改（status: loading）
  // 成功：不改 VM，跳转到新会话
  // 失败：Notice：改（status: failed, text）
  private async createConversation(): Promise<void> {
    this.createConversationController?.abort();
    this.createConversationController = new AbortController();
    const { signal } = this.createConversationController;

    this.notice.set({ status: 'loading', text: 'Creating conversation…' });

    try {
      const conversationId = await this.agent.createConversation(signal);
      // replaceUrl：后退时不会回到 /conversations 又创建一个会话
      await this.router.navigate(['/conversations', conversationId], { replaceUrl: true });
    } catch (error) {
      if (isAbortError(error)) return;
      this.notice.set({ status: 'failed', text: describeError(error) });
    }
  }
}
