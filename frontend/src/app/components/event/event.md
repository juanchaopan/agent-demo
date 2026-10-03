# Event 组件

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | `EventVM` | 整个配置对象 |
| `.status` | `'loading' \| 'loaded' \| 'failed'` | 事件数据的加载状态 |
| `.data` | `unknown` | 事件数据，任意可 JSON 序列化的值；`null` 表示还没有事件。只在 `loaded` 时使用 |
| `.error` | `string \| null` | 加载失败时的错误提示。只在 `failed` 时使用 |

## 输出
无。组件只负责展示。

## 双向绑定
无。

## 视觉状态

| Status | Data | Error | 加载动画 | 错误红字 | 内容区 |
|--------|------|-------|---------|---------|--------|
| `loading` | 任何 | 任何 | 显示 | 隐藏 | 隐藏 |
| `failed` | 任何 | 任何 | 隐藏 | 显示 | 隐藏 |
| `loaded` | `null` | 任何 | 隐藏 | 隐藏 | 空状态提示 |
| `loaded` | 非 `null` | 任何 | 隐藏 | 隐藏 | 显示 JSON |

## 大小与布局

- **Width**：`w-full`，撑满父容器
- **Height**：`h-fit`，按内容高度
- **Margin**：未设置，紧贴父容器边框

## 父组件集成示例

```html
<div [event]="event()"></div>
```

```typescript
protected readonly event = signal<EventVM>({ status: 'loading', data: null, error: null });

private async loadEvent(id: string): Promise<void> {
  this.event.set({ status: 'loading', data: null, error: null });
  try {
    const data = await this.api.getEvent(id);
    this.event.set({ status: 'loaded', data, error: null });
  } catch (error) {
    this.event.set({ status: 'failed', data: null, error: String(error) });
  }
}
```
