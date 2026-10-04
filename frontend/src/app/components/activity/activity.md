# Activity 组件

AI 回复里的"本轮改动记录"面板：一条折叠条，点开后逐条列出对表单的改动尝试。

## 输入

| 字段 | 类型 | 说明 |
|------|------|------|
| `activity` | `ActivityVM` | 整个配置对象 |
| `.items` | `readonly ActivityItem[]` | 改动记录，按数组顺序显示；为空时组件不渲染任何东西 |
| `.items[i].field` | `string` | 字段路径，如 `title`、`awards[0].cashValue`；`submit` 时为空串 |
| `.items[i].operation` | `'set' \| 'add' \| 'remove' \| 'submit'` | 设值 / 往列表追加 / 从列表移除（`value` 是下标）/ 提交整个表单 |
| `.items[i].value` | `unknown` | 任意 JSON 值；`submit` 时为 `null`，不显示 |
| `.items[i].status` | `'applied' \| 'rejected'` | 是否生效 |
| `.items[i].error` | `string \| null` | `rejected` 时的原因 |
| `.expanded` | `boolean` | 是否展开明细 |

## 输出

| 事件 | 参数 | 何时触发 | 父组件应该 |
|------|------|----------|-----------|
| `toggle` | 无（`void`） | 用户点了折叠条 | 把 `expanded` 取反；纯本地 UI 状态，任何时候都响应 |

## 双向绑定
无。

## 视觉状态

| Items | Expanded | 折叠条 | 明细列表 |
|-------|----------|--------|---------|
| 空 | 任何 | 隐藏 | 隐藏 |
| 非空 | `false` | 显示 | 隐藏 |
| 非空 | `true` | 显示 | 显示 |

明细列表里，每一行：

| Status | 行 | 错误原因 |
|--------|----|---------|
| `applied` | 正常 | 隐藏 |
| `rejected` | 警示 | 显示 |

折叠条概括文案（"更新项"指 `operation` 不是 `submit` 的项，N 为个数）：

| 部分 | 规则 | 样式 |
|------|------|------|
| 成功部分 | 成功的更新项 N > 0 → `updated N field` / `updated N fields`（N = 1 时单数）；有成功的 `submit` → `submitted`；两者用 ` and ` 连接，首字母大写 | 正常 |
| 失败部分 | 被拒的更新项 N > 0 → `N not applied`；有被拒的 `submit` → `not submitted`；两者用 `, ` 连接，首字母大写 | 警示 |
| 拼接 | 两部分中非空的用 ` · ` 连接 | — |

例：`Updated 3 fields`、`Updated 2 fields · 1 not applied`、`Submitted`、`Updated 2 fields and submitted`、`Not submitted`。

明细行文案：`标签 字段 值`，字段为空串时不显示。

| Operation | 标签 | 值 |
|-----------|------|----|
| `set` | `Set` | 按下表格式化 |
| `add` | `Add` | 按下表格式化 |
| `remove` | `Remove` | 非负整数下标 → `#下标+1`；否则按下表格式化 |
| `submit` | `Submit form` | 不显示 |

| Value | 显示 |
|-------|------|
| `null` | `(cleared)` |
| 字符串 | 加引号 `“…”`；空串显示 `“”` |
| 数字、布尔 | 原样（`0`、`true`、`false`） |
| 对象、数组 | 紧凑 JSON |

字符串和 JSON 超过 80 个字符时截断并加 `…`；长值可在任意位置换行，不会撑破父容器。

## 大小与布局

- **Width**：`w-full`，撑满父容器
- **Height**：按内容高度；`items` 为空时高度为 0
- **Margin**：`items` 非空时下方有 `mb-2`，与后面的内容隔开；为空时没有 margin，不占任何空间
- **Display**：`block`

## 父组件集成示例

```html
<div [activity]="activity()" (toggle)="onToggle()"></div>
```

```typescript
protected readonly activity = signal<ActivityVM>({ items: [], expanded: false });

private async load(): Promise<void> {
  const items = await this.api.getActivity();
  this.activity.update((a) => ({ ...a, items: [...a.items, ...items] }));
}

protected onToggle(): void {
  this.activity.update((a) => ({ ...a, expanded: !a.expanded }));
}
```
