# Conversation 页面

## 加载全部消息 `loadMessages`

| 开始 | 成功 | 失败 |
|------|------|------|
| `Messages: loading`<br>`Composer: disabled` | `Messages: ready`<br>`Composer: ready` | `Messages: failed`<br>`Composer: disabled` |

## 发消息 `postMessage` → `loadMessagesFrom`

| 开始 | 成功 | 发送失败 | 加载失败 |
|------|------|---------|---------|
| `Composer: submitting` | `Composer: ready` | `Composer: ready` | `Composer: disabled` |

## 单条重试 `loadMessagesFrom`

| 开始 | 成功 | 失败 |
|------|------|------|
| `Composer: submitting` | `Composer: ready` | `Composer: disabled` |

## 加载 event `loadEvent`

| 开始 | 成功 | 失败 |
|------|------|------|
| `Event: loading` | `Event: loaded` | `Event: failed` |
