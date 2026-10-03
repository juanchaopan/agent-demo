# Page Comment Style

For page files. Write comments in Chinese, plain technical language. Every commented block starts with a kind line.

## 1. Kind line

| Kind | Applies to |
|------|-----------|
| `Entry point：` | `effect`, its `onCleanup`, handlers bound to child outputs |
| `Workflow：` | one API operation that sets VM status at start / success / failure |
| `Callback：` | local functions a workflow calls or passes to the API |

## 2. Entry points

Kind line, then up to 3 lines:

```
// Entry point：
// <什么时候触发>，<整体干什么>：
//   - <类型> <名字>：<含义>        ← one line each
// 大白话讲具体做了什么和要点
```

| Entry point | 触发 | 列表行 |
|-------------|------|--------|
| `effect` | `监听 N 个东西，任一变化就…` | 监听对象，类型为 `输入` / `XxxVM`；只列真正读到的 signal |
| `onCleanup` | `<输入>变化或页面销毁时，…` | 无 |
| handler | `用户 <操作> 时，…` | 参数 |

## 3. Workflows

```
// Workflow：<一句话说这个工作流是什么>
// 返回：<返回值含义，void 写"无">
//   - <参数>：<含义>          ← one line per parameter
// 开始：<VM>：<增/删/改>（<字段或说明>）；<VM>：...      ← 省略，若 try 之前不改 VM
// 成功：<VM>：<增/删/改>（<字段或说明>）；<VM>：...
// 失败：<VM>：<增/删/改>（<字段或说明>）；<VM>：...
// 收尾：<VM>：<增/删/改>（<字段或说明>）；<VM>：...      ← 省略，若没有 finally
```

开始/成功/失败/收尾只列这个工作流改动的 VM（包括它调用或传给 API 的 Callback 改动的），按增/删/改分类，不写触发时机、调用者、abort 相关的判断。

## 4. Callbacks

One line: `Callback：每<触发时机>，改 XxxVM 的 <字段>：<规则>`

Only this function's own rule. No callers, no other components, no business background.
