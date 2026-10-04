import { Component, computed, input, output } from '@angular/core';
import { ActivityItem, ActivityVM } from './activity-vm';

interface SummaryPart {
  text: string;
  rejected: boolean;
}

interface ActivityRow {
  label: string;
  field: string;
  detail: string | null;
  rejected: boolean;
  error: string | null;
}

const OPERATION_LABELS: Record<ActivityItem['operation'], string> = {
  set: 'Set',
  add: 'Add',
  remove: 'Remove',
  submit: 'Submit form',
};

const MAX_VALUE_LENGTH = 80;

@Component({
  selector: 'div[activity]',
  templateUrl: './activity-component.html',
  host: {
    class: 'block w-full',
    '[class.mb-2]': 'visible()',
  },
})
export class ActivityComponent {
  readonly activity = input.required<ActivityVM>();
  readonly toggle = output<void>();

  protected readonly visible = computed(() => this.activity().items.length > 0);

  protected readonly summaryParts = computed<SummaryPart[]>(() => {
    const items = this.activity().items;
    const updated = this.count(items, false, 'applied');
    const notApplied = this.count(items, false, 'rejected');
    const submitted = this.count(items, true, 'applied') > 0;
    const notSubmitted = this.count(items, true, 'rejected') > 0;

    const applied = this.join(
      [
        updated > 0 ? `updated ${updated} ${updated === 1 ? 'field' : 'fields'}` : '',
        submitted ? 'submitted' : '',
      ],
      ' and ',
    );
    const rejected = this.join(
      [notApplied > 0 ? `${notApplied} not applied` : '', notSubmitted ? 'not submitted' : ''],
      ', ',
    );

    return [
      { text: applied, rejected: false },
      { text: rejected, rejected: true },
    ].filter((part) => part.text);
  });

  protected readonly rows = computed<ActivityRow[]>(() =>
    this.activity().items.map((item) => ({
      label: OPERATION_LABELS[item.operation] ?? item.operation,
      field: item.field,
      detail: this.describeValue(item),
      rejected: item.status === 'rejected',
      error: item.error,
    })),
  );

  private count(
    items: readonly ActivityItem[],
    submit: boolean,
    status: ActivityItem['status'],
  ): number {
    return items.filter(
      (item) => (item.operation === 'submit') === submit && item.status === status,
    ).length;
  }

  private join(texts: string[], separator: string): string {
    const text = texts.filter((t) => t).join(separator);
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  private describeValue({ operation, value }: ActivityItem): string | null {
    if (operation === 'submit') return null;
    if (
      operation === 'remove' &&
      typeof value === 'number' &&
      Number.isInteger(value) &&
      value >= 0
    ) {
      return `#${value + 1}`;
    }
    return this.formatValue(value);
  }

  private formatValue(value: unknown): string {
    if (value === null || value === undefined) return '(cleared)';
    if (typeof value === 'string') return `“${this.truncate(value)}”`;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    return this.truncate(JSON.stringify(value));
  }

  private truncate(text: string): string {
    const chars = Array.from(text);
    return chars.length > MAX_VALUE_LENGTH
      ? `${chars.slice(0, MAX_VALUE_LENGTH).join('')}…`
      : text;
  }
}
