# UserMessage 组件

用户发出的消息气泡，靠右显示。

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `userMessage` | `UserMessageVM` | 整个配置对象 |
| `.id` | `string` | 消息 ID。组件本身不使用，供父组件识别是哪条消息 |
| `.role` | `'user'` | 固定值。组件本身不使用，供父组件区分消息类型 |
| `.status` | `'streaming' \| 'done' \| 'failed'` | 消息的生成状态 |
| `.content` | `string` | 消息文字；流式生成时逐步追加 |

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `retry` | 无（`void`） | 用户点了 `failed` 消息上的 Retry | 从这条消息起重新拉取，并把 `status` 依次更新为 `streaming` → `done` / `failed` |

## 双向绑定
无。

## 视觉状态

| Status | Content | 生成指示 | 错误提示 + Retry | 消息文字 |
|--------|---------|---------|-----------------|---------|
| `streaming` | 空 | 加载中 | 隐藏 | 隐藏 |
| `streaming` | 非空 | 加载中（接在文字末尾） | 隐藏 | 显示 |
| `done` | 任何 | 隐藏 | 隐藏 | 有值就显示 |
| `failed` | 任何 | 隐藏 | 显示 | 有值就显示 |

`done` 且 `content` 为空时，只剩一个空气泡。

## 大小与布局

- **Width**：`w-fit`，按内容宽度，最多为父容器的 95%（`max-w-[95%]`）
- **Height**：`h-fit`，按内容高度
- **Margin**：未设置，紧贴父容器边框
- **Display**：靠右用的是 `self-end`，父容器必须是 flex 布局才生效（如 `messages` 组件的 `flex-col`）；否则靠左

## 父组件集成示例

```html
<div class="flex flex-col">
  <div [userMessage]="message()" (retry)="onRetry()"></div>
</div>
```

```typescript
protected readonly message = signal<UserMessageVM>({ id: 'm1', role: 'user', status: 'streaming', content: '' });

private async load(): Promise<void> {
  this.message.update((m) => ({ ...m, status: 'streaming', content: '' }));
  try {
    for await (const chunk of this.api.streamMessage(this.message().id)) {
      this.message.update((m) => ({ ...m, content: m.content + chunk }));
    }
    this.message.update((m) => ({ ...m, status: 'done' }));
  } catch {
    this.message.update((m) => ({ ...m, status: 'failed' }));
  }
}

protected onRetry(): void {
  void this.load();
}
```
