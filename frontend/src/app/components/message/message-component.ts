import { Component, computed, input, output } from '@angular/core';
import { MessageVM } from './message-vm';

@Component({
  selector: 'div[message]',
  templateUrl: './message-component.html',
  host: {
    class: 'h-fit w-fit max-w-[95%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed break-words',
    '[class]': 'variantClass()',
  },
})
export class MessageComponent {
  readonly message = input.required<MessageVM>();
  readonly retry = output<void>();

  protected readonly isUser = computed(() => this.message().role === 'user');

  protected readonly variantClass = computed(() =>
    this.isUser()
      ? 'self-end rounded-br-md bg-slate-900 text-white'
      : 'self-start rounded-bl-md border border-slate-200 bg-white text-slate-800 shadow-sm',
  );
}
