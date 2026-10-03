import { Component, computed, model, output } from '@angular/core';
import { ComposerVM } from './composer-vm';

@Component({
  selector: 'div[composer]',
  templateUrl: './composer-component.html',
  host: {
    class:
      'flex h-fit w-full items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 text-sm shadow-sm focus-within:border-slate-400',
    '[class]': 'variantClass()',
  },
})
export class ComposerComponent {
  readonly composer = model.required<ComposerVM>();
  readonly submit = output<string>();

  protected readonly isDisabled = computed(() => this.composer().status === 'disabled');
  protected readonly isSubmitting = computed(() => this.composer().status === 'submitting');

  protected readonly canSubmit = computed(
    () => this.composer().status === 'ready' && this.composer().draft.trim().length > 0,
  );

  protected readonly variantClass = computed(() => (this.isDisabled() ? 'opacity-60' : ''));

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      this.onSubmit();
    }
  }

  protected onInput(value: string): void {
    this.composer.update((composer) => ({ ...composer, draft: value, error: null }));
  }

  protected onSubmit(): void {
    if (!this.canSubmit()) return;

    this.composer.update((composer) => ({ ...composer, error: null }));
    this.submit.emit(this.composer().draft.trim());
  }
}
