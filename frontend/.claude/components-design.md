# Angular 组件最佳实践：受控组件模式

## 核心原则
组件 = 纯 Input → Computed → Output

所有状态存放在父组件（page 层）。组件永远不修改 input 也不管理状态。

## 数据架构

### name-vm.ts
定义数据结构
```typescript
interface NameVM {
  status: string;
  data: any;
}
```

### name-component.ts
**Input（单向）**
```typescript
readonly name = input.required<NameVM>();
```

**Output（业务事件）**
```typescript
readonly onSubmit = output<string>();
```

**或用 model()（双向绑定）**
```typescript
readonly name = model.required<NameVM>();
```

**内部逻辑**
```typescript
protected readonly isDisabled = computed(() => this.name().status === 'disabled');
protected onSubmitClick() { this.onSubmit.emit(this.name().data); }
```

### name-component.html
```html
<!-- 单向绑定 input -->
<div [name]="name()"></div>

<!-- 双向绑定 model() -->
<div [(name)]="name"></div>

<!-- 事件触发 TS 函数 -->
<button (click)="onSubmitClick()">Send</button>

<!-- 事件直接触发 output emit -->
<button (click)="onSubmit.emit(name().data)">Quick Send</button>
```

## 模板规则
- 只绑定：`input` 或 `computed()`
- 事件：`(click)="onSubmit()"` 或 `(event)="output.emit(data)"`
- 模板里不写复杂逻辑

## 视觉和间距（从调用者角度）

父组件关心的：
- **宽度**：撑满父容器 / 按内容 / 固定宽度
- **高度**：撑满父容器 / 按内容 / 固定高度
- **Margin**：外部间距（上右下左）
- **Display**：在父布局中的角色（block、inline、flex-item）

子元素内部的排列 = 组件自己的事。

## 每个组件的文档应该包括

| 部分 | 内容 |
|------|------|
| **Input** | VM 里的字段、类型、说明 |
| **Output** | 事件名、参数、何时触发、父组件的预期处理 |
| **Visuals** | 状态矩阵：input 组合 → 显示效果 |
| **Sizing** | 宽度、高度、margin 的行为 |
| **Parent Code** | 示例：怎么传 input、怎么处理 output |

## 为什么选这个模式

✅ 单向数据流（易于调试）
✅ 父组件拥有状态（无隐藏逻辑）
✅ 高复用性（同一组件、不同状态管理）
✅ 易测试（input → output，无副作用）
✅ 易扩展（组件间契约清晰）

## 禁止做的

❌ 组件修改自己的 input
❌ 组件直接调用 API
❌ 用本地 signal 存业务数据
❌ 绑定到父组件的内部 signal
❌ 模板里写复杂表达式
