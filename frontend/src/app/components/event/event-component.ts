import { Component, input } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { EventVM } from './event-vm';

@Component({
  selector: 'div[event]',
  imports: [JsonPipe],
  templateUrl: './event-component.html',
  host: {
    class: 'flex h-fit w-full flex-col gap-3 p-4 text-sm',
  },
})
export class EventComponent {
  readonly event = input.required<EventVM>();
}
