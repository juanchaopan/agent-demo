# Messages 组件

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | `MessagesVM` | 整个配置对象 |
| `.status` | `'loading' \| 'ready' \| 'failed'` | 列表整体状态，决定显示哪种视图 |
| `.error` | `string \| null` | `failed` 时显示的错误信息 |
| `.items` | `readonly MessageVM[]` | 消息列表，按数组顺序显示；`MessageVM` 是 `UserMessageVM \| AssistantMessageVM` |
| `.items[i].id` | `string` | 消息 ID，用作列表 `track` 的 key，也是 `retry`、`toggleActivity` 事件的参数 |
| `.items[i].role` | `'user' \| 'assistant'` | `user` 交给 `userMessage` 组件显示，`assistant` 交给 `assistantMessage` 组件显示；其余字段见这两个组件 |

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `retry` | `string \| null` | 用户点了 Retry：整体加载失败时发 `null`，某条用户消息失败时发它的 `id` | 从该消息起重新拉取；`null` 表示从头重新加载 |
| `toggleActivity` | `string` | 用户点了某条 AI 消息改动记录面板的折叠条，发它的 `id` | 把这条消息的 `expanded` 取反；纯本地 UI 状态，不发请求，任何状态下都响应 |

## 双向绑定
无。

## 视觉状态

| Status | Items | 加载提示 | 错误 + 重试 | 空状态提示 | 消息列表 |
|--------|-------|---------|------------|-----------|---------|
| `loading` | 任何 | 显示 | 隐藏 | 隐藏 | 隐藏 |
| `failed` | 任何 | 隐藏 | 显示 | 隐藏 | 隐藏 |
| `ready` | 空 | 隐藏 | 隐藏 | 显示 | 隐藏 |
| `ready` | 非空 | 隐藏 | 隐藏 | 隐藏 | 显示 |

## 大小与布局

- **Width**：`w-full`，撑满父容器
- **Height**：`h-full`，撑满父容器
- **Margin**：未设置，紧贴父容器边框

## 父组件集成示例

```html
<div
  class="min-h-0 flex-1"
  [messages]="messages()"
  (retry)="onRetry($event)"
  (toggleActivity)="onToggleActivity($event)"
></div>
```

```typescript
protected readonly messages = signal<MessagesVM>({ status: 'loading', error: null, items: [] });

protected async onRetry(fromId: string | null): Promise<void> {
  if (fromId === null) this.messages.set({ status: 'loading', error: null, items: [] });
  try {
    const items = await this.api.getMessages(this.id(), fromId);
    this.messages.update((m) => ({ status: 'ready', error: null, items: [...m.items, ...items] }));
  } catch (error) {
    if (fromId === null) {
      this.messages.update((m) => ({ ...m, status: 'failed', error: String(error) }));
    } else {
      this.messages.update((m) => ({
        ...m,
        items: m.items.map((item) => (item.id === fromId ? { ...item, status: 'failed' } : item)),
      }));
    }
  }
}

protected onToggleActivity(id: string): void {
  this.messages.update((m) => ({
    ...m,
    items: m.items.map((item) =>
      item.id === id && item.role === 'assistant' ? { ...item, expanded: !item.expanded } : item,
    ),
  }));
}
```
