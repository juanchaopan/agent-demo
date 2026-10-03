import { MessageVM } from '../message/message-vm';

export type MessagesStatus = 'loading' | 'ready' | 'failed';

export interface MessagesVM {
  status: MessagesStatus;
  error: string | null;
  items: readonly MessageVM[];
}
