import { Routes } from '@angular/router';
import { ConversationPage } from './pages/conversation/conversation-page';
import { NewConversationPage } from './pages/new-conversation/new-conversation-page';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'conversations' },
  { path: 'conversations', component: NewConversationPage },
  { path: 'conversations/:id', component: ConversationPage },
];
