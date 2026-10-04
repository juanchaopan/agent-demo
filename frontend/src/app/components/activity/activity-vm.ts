export interface ActivityItem {
  field: string;
  operation: 'set' | 'add' | 'remove' | 'submit';
  value: unknown;
  status: 'applied' | 'rejected';
  error: string | null;
}

export interface ActivityVM {
  items: readonly ActivityItem[];
  expanded: boolean;
}
