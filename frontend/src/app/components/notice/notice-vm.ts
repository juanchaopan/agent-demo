export type NoticeStatus = 'loading' | 'failed';

export interface NoticeVM {
  status: NoticeStatus;
  text: string;
}
