export type MessageRole = 'user' | 'assistant';

export type MessageStatus = 'streaming' | 'done' | 'failed';

export interface MessageVM {
  id: string;
  role: MessageRole;
  status: MessageStatus;
  content: string;
}
