export type UserMessageStatus = 'streaming' | 'done' | 'failed';

export interface UserMessageVM {
  id: string;
  role: 'user';
  status: UserMessageStatus;
  content: string;
}
