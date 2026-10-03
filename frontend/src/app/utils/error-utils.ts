/**
 * Whether an error was thrown because a request was cancelled via AbortController
 * @example
 * const controller = new AbortController();
 * try {
 *   await fetch('/slow', { signal: controller.signal });
 * } catch (error) {
 *   if (isAbortError(error)) return; // cancelled on purpose, not a real failure
 *   throw error;
 * }
 */
export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

/**
 * Turn any thrown value into a message that can be shown to the user
 * @example
 * describeError(new Error('Network down'));
 * // → 'Network down'
 * describeError('oops');
 * // → 'Something went wrong'
 */
export function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong';
}
