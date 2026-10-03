export type ComposerStatus = 'ready' | 'submitting' | 'disabled';

export interface ComposerVM {
  status: ComposerStatus;
  draft: string;
  error: string | null;
}
