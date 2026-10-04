import { ActivityItem } from '../activity/activity-vm';

export type AssistantMessageStatus = 'streaming' | 'done' | 'failed';

export interface AssistantMessageVM {
  id: string;
  role: 'assistant';
  status: AssistantMessageStatus;
  content: string;
  activity: readonly ActivityItem[];
  expanded: boolean;
}
