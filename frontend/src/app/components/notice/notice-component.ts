import { Component, input } from '@angular/core';
import { NoticeVM } from './notice-vm';

@Component({
  selector: 'div[notice]',
  templateUrl: './notice-component.html',
  host: {
    class: 'h-fit w-full text-center text-sm',
  },
})
export class NoticeComponent {
  readonly notice = input.required<NoticeVM>();
}
