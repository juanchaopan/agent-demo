# Notice 组件

## 输入

| 字段      | 类型                    | 说明                       |
| --------- | ----------------------- | -------------------------- |
| `notice`  | `NoticeVM`              | 整个配置对象               |
| `.status` | `'loading' \| 'failed'` | 提示的类型，决定文字的样式 |
| `.text`   | `string`                | 要显示的文字               |

## 输出

无。组件只负责展示。

## 双向绑定

无。

## 视觉状态

| Status    | 提示文字 | 错误文字 |
| --------- | -------- | -------- |
| `loading` | 显示     | 隐藏     |
| `failed`  | 隐藏     | 显示     |

## 大小与布局

- **Width**：`w-full`，撑满父容器
- **Height**：`h-fit`，按内容高度
- **Margin**：未设置，紧贴父容器边框

## 父组件集成示例

```html
<div [notice]="notice()"></div>
```

```typescript
protected readonly notice = signal<NoticeVM>({ status: 'loading', text: 'Working…' });

private async work(): Promise<void> {
  this.notice.set({ status: 'loading', text: 'Working…' });
  try {
    await this.api.doWork();
  } catch (error) {
    this.notice.set({ status: 'failed', text: String(error) });
  }
}
```
