import { AssistantMessageVM } from '../assistant-message/assistant-message-vm';
import { UserMessageVM } from '../user-message/user-message-vm';

export type MessageVM = UserMessageVM | AssistantMessageVM;

export type MessageStatus = MessageVM['status'];

export type MessagesStatus = 'loading' | 'ready' | 'failed';

export interface MessagesVM {
  status: MessagesStatus;
  error: string | null;
  items: readonly MessageVM[];
}
