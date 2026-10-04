import { Component, computed, input, output } from '@angular/core';
import { ActivityComponent } from '../activity/activity-component';
import { ActivityVM } from '../activity/activity-vm';
import { AssistantMessageVM } from './assistant-message-vm';

@Component({
  selector: 'div[assistantMessage]',
  imports: [ActivityComponent],
  templateUrl: './assistant-message-component.html',
  host: {
    class:
      'h-fit w-fit max-w-[95%] self-start rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-2.5 text-sm leading-relaxed break-words text-slate-800 shadow-sm',
  },
})
export class AssistantMessageComponent {
  readonly assistantMessage = input.required<AssistantMessageVM>();
  readonly toggleActivity = output<void>();

  protected readonly activity = computed<ActivityVM>(() => ({
    items: this.assistantMessage().activity,
    expanded: this.assistantMessage().expanded,
  }));
}
