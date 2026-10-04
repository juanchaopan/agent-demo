import { Component, input, output } from '@angular/core';
import { UserMessageVM } from './user-message-vm';

@Component({
  selector: 'div[userMessage]',
  templateUrl: './user-message-component.html',
  host: {
    class:
      'h-fit w-fit max-w-[95%] self-end rounded-2xl rounded-br-md bg-slate-900 px-4 py-2.5 text-sm leading-relaxed break-words text-white',
  },
})
export class UserMessageComponent {
  readonly userMessage = input.required<UserMessageVM>();
  readonly retry = output<void>();
}
