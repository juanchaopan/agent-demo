export type EventStatus = 'loading' | 'loaded' | 'failed';

export interface EventVM {
  status: EventStatus;
  data: unknown;
  error: string | null;
}
