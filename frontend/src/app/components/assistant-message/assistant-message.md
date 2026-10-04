# AssistantMessage 组件

AI 回复的气泡，靠左显示；正文上方挂一个可折叠的改动记录面板（`activity` 组件）。

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `assistantMessage` | `AssistantMessageVM` | 整个配置对象 |
| `.id` | `string` | 消息 ID。组件本身不使用，供父组件识别是哪条消息 |
| `.role` | `'assistant'` | 固定值。组件本身不使用，供父组件区分消息类型 |
| `.status` | `'streaming' \| 'done' \| 'failed'` | 消息的生成状态 |
| `.content` | `string` | 消息文字；流式生成时逐步追加 |
| `.activity` | `readonly ActivityItem[]` | 本轮改动记录，按顺序追加；格式见 `activity` 组件 |
| `.expanded` | `boolean` | 改动记录面板是否展开 |

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `toggleActivity` | 无（`void`） | 用户点了改动记录面板的折叠条 | 把这条消息的 `expanded` 取反；纯本地 UI 状态，不发请求，`streaming` / `failed` 时也照常响应 |

## 双向绑定
无。

## 视觉状态

| Status | Content | 生成指示 | 错误提示 | 消息文字 |
|--------|---------|---------|---------|---------|
| `streaming` | 空 | 加载中 | 隐藏 | 隐藏 |
| `streaming` | 非空 | 加载中（接在文字末尾） | 隐藏 | 显示 |
| `done` | 任何 | 隐藏 | 隐藏 | 有值就显示 |
| `failed` | 任何 | 隐藏 | 显示 | 有值就显示 |

改动记录面板在消息文字上方，与 `status`、`content` 无关：

| Activity | Expanded | 折叠条 | 明细列表 |
|----------|----------|--------|---------|
| 空 | 任何 | 隐藏 | 隐藏 |
| 非空 | `false` | 显示 | 隐藏 |
| 非空 | `true` | 显示 | 显示 |

`done`、`content` 为空、`activity` 为空时，只剩一个空气泡。

## 大小与布局

- **Width**：`w-fit`，按内容宽度，最多为父容器的 95%（`max-w-[95%]`）
- **Height**：`h-fit`，按内容高度
- **Margin**：未设置，紧贴父容器边框
- **Display**：靠左用的是 `self-start`，父容器必须是 flex 布局才生效（如 `messages` 组件的 `flex-col`）

## 父组件集成示例

```html
<div class="flex flex-col">
  <div [assistantMessage]="message()" (toggleActivity)="onToggleActivity()"></div>
</div>
```

```typescript
protected readonly message = signal<AssistantMessageVM>({
  id: 'm1',
  role: 'assistant',
  status: 'streaming',
  content: '',
  activity: [],
  expanded: false,
});

private async generate(): Promise<void> {
  this.message.update((m) => ({ ...m, status: 'streaming', content: '', activity: [], expanded: false }));
  try {
    const activity = await this.api.getActivity(this.message().id);
    this.message.update((m) => ({ ...m, activity: [...m.activity, ...activity] }));
    for await (const chunk of this.api.streamMessage(this.message().id)) {
      this.message.update((m) => ({ ...m, content: m.content + chunk }));
    }
    this.message.update((m) => ({ ...m, status: 'done' }));
  } catch {
    this.message.update((m) => ({ ...m, status: 'failed' }));
  }
}

protected onToggleActivity(): void {
  this.message.update((m) => ({ ...m, expanded: !m.expanded }));
}
```
