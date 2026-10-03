export interface SseMessage {
  event: string;
  data: string;
}

/**
 * Read a Server-Sent Events response as an async stream of messages
 * @example
 * const res = await fetch('/ticker', { headers: { Accept: 'text/event-stream' } });
 * for await (const { event, data } of readSse(res)) {
 *   console.log(event, data); // 'message' '{"price":42}'
 * }
 */
export async function* readSse(res: Response): AsyncGenerator<SseMessage> {
  if (!res.body) throw new Error('Response has no body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) return;

      buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, '\n');
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';

      for (const frame of frames) {
        const message = parseFrame(frame);
        if (message) yield message;
      }
    }
  } finally {
    reader.cancel().catch(() => undefined);
  }
}

function parseFrame(frame: string): SseMessage | null {
  let event = 'message';
  const data: string[] = [];

  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = fieldValue(line, 'event:');
    else if (line.startsWith('data:')) data.push(fieldValue(line, 'data:'));
  }

  return data.length > 0 ? { event, data: data.join('\n') } : null;
}

function fieldValue(line: string, field: string): string {
  return line.slice(field.length).replace(/^ /, '');
}
