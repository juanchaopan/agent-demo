import { Component } from '@angular/core';
import { ConversationPage } from './conversation-page/conversation-page';

@Component({
  imports: [ConversationPage],
  selector: 'app-root',
  templateUrl: './app.html',
})
export class App {}
