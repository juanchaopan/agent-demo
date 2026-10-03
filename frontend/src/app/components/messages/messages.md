# Messages 组件

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | `MessagesVM` | 整个配置对象 |
| `.status` | `'loading' \| 'ready' \| 'failed'` | 列表整体状态，决定显示哪种视图 |
| `.error` | `string \| null` | `failed` 时显示的错误信息 |
| `.items` | `readonly MessageVM[]` | 消息列表，按数组顺序显示；每条的显示细节见 `message` 组件 |
| `.items[i].id` | `string` | 消息 ID，用作列表 `track` 的 key，也是 `retry` 事件的参数 |

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `retry` | `string \| null` | 用户点了 Retry：整体加载失败时发 `null`，某条用户消息失败时发它的 `id` | 从该消息起重新拉取；`null` 表示从头重新加载 |

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
<div class="min-h-0 flex-1" [messages]="messages()" (retry)="onRetry($event)"></div>
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
```
