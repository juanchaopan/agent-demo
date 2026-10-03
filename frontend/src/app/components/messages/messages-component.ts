import { Component, ElementRef, effect, inject, input, output } from '@angular/core';
import { MessageComponent } from '../message/message-component';
import { MessagesVM } from './messages-vm';

@Component({
  selector: 'div[messages]',
  imports: [MessageComponent],
  templateUrl: './messages-component.html',
  host: {
    class: 'block h-full w-full overflow-y-auto',
  },
})
export class MessagesComponent {
  readonly messages = input.required<MessagesVM>();
  readonly retry = output<string | null>();

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;

  constructor() {
    effect(() => {
      this.messages();
      requestAnimationFrame(() => this.host.scrollTo({ top: this.host.scrollHeight }));
    });
  }
}
