# Composer 组件

## 输入
无。使用双向绑定。

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `submit` | `string` | 用户按 Enter 或点发送按钮 | 发送内容；期间 `status` 设为 `submitting`，成功后清空 `draft`，失败时写入 `error` |

## 双向绑定

| 字段 | 类型 | 说明 |
|------|------|------|
| `composer` | `ComposerVM` | 整个配置对象，`model()` 形式 |
| `.status` | `'ready' \| 'submitting' \| 'disabled'` | 输入框是否可用 |
| `.draft` | `string` | 输入框里的文字内容 |
| `.error` | `string \| null` | 发送失败时的错误提示 |

## 视觉状态

| Status | Draft | Error | 输入框 | 发送按钮 | 错误红字 |
|--------|-------|-------|--------|---------|---------|
| `disabled` | 任何 | 任何 | 禁用 | 禁用 | 有值就显示 |
| `ready` | 空 | 任何 | 可用 | 禁用 | 有值就显示 |
| `ready` | 非空 | 任何 | 可用 | 可用 | 有值就显示 |
| `submitting` | 任何 | 任何 | 可用 | 加载中 | 有值就显示 |

## 大小与布局

- **Width**：`w-full`，撑满父容器
- **Height**：`h-fit`，按内容高度
- **Margin**：未设置，紧贴父容器边框

## 父组件集成示例

```html
<div [(composer)]="composer" (submit)="onSubmit($event)"></div>
```

```typescript
protected readonly composer = signal<ComposerVM>({ status: 'disabled', draft: '', error: null });

private async init(): Promise<void> {
  await this.api.connect();
  this.composer.update((c) => ({ ...c, status: 'ready' }));
}

protected async onSubmit(content: string): Promise<void> {
  this.composer.update((c) => ({ ...c, status: 'submitting' }));
  try {
    await this.api.sendMessage(content);
    this.composer.update((c) => ({ ...c, status: 'ready', draft: '' }));
  } catch (error) {
    this.composer.update((c) => ({ ...c, status: 'ready', error: String(error) }));
  }
}
```
