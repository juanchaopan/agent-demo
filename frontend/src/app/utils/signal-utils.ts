import { WritableSignal } from '@angular/core';

/**
 * Update multiple fields in a signal's value
 * @example
 * const product = signal({ name: 'Apple', price: 1.5, stock: 10 });
 * patch(product, { price: 1.99, stock: 8 });
 * // product() → { name: 'Apple', price: 1.99, stock: 8 }
 */
export function patch<T extends object>(target: WritableSignal<T>, changes: Partial<T>): void {
  target.update((value) => ({ ...value, ...changes }));
}

/**
 * Update a single field using a transform function
 * @example
 * const counter = signal({ count: 5, label: 'Clicks' });
 * updateField(counter, 'count', (count) => count + 1);
 * // counter() → { count: 6, label: 'Clicks' }
 */
export function updateField<T extends object, K extends keyof T>(
  target: WritableSignal<T>,
  key: K,
  fn: (value: T[K]) => T[K],
): void {
  target.update((value) => ({ ...value, [key]: fn(value[key]) }));
}

/**
 * Find the first item whose `key` field equals `value`
 * @example
 * const fruits = [{ name: 'apple', color: 'red' }, { name: 'banana', color: 'yellow' }];
 * findBy(fruits, 'color', 'yellow');
 * // → { name: 'banana', color: 'yellow' }
 */
export function findBy<T, K extends keyof T>(
  items: readonly T[],
  key: K,
  value: T[K],
): T | undefined {
  return items.find((item) => item[key] === value);
}

/**
 * Append items to the end
 * @example
 * append([1, 2], 3, 4);
 * // → [1, 2, 3, 4]
 */
export function append<T>(items: readonly T[], ...added: T[]): readonly T[] {
  return [...items, ...added];
}

/**
 * Insert items at an index
 * @example
 * insertAt(['a', 'c'], 1, 'b');
 * // → ['a', 'b', 'c']
 */
export function insertAt<T>(items: readonly T[], index: number, ...added: T[]): readonly T[] {
  return [...items.slice(0, index), ...added, ...items.slice(index)];
}

/**
 * Transform every item matching a predicate
 * @example
 * const todos = [{ title: 'Buy milk', done: false }, { title: 'Walk dog', done: false }];
 * updateWhere(todos, (t) => !t.done, (t) => ({ ...t, done: true }));
 * // → [{ title: 'Buy milk', done: true }, { title: 'Walk dog', done: true }]
 */
export function updateWhere<T>(
  items: readonly T[],
  predicate: (item: T, index: number) => boolean,
  fn: (item: T) => T,
): readonly T[] {
  return items.map((item, index) => (predicate(item, index) ? fn(item) : item));
}

/**
 * Transform every item whose `key` field equals `value`
 * @example
 * const todos = [{ title: 'Buy milk', done: false }, { title: 'Walk dog', done: false }];
 * updateBy(todos, 'title', 'Buy milk', (t) => ({ ...t, done: true }));
 * // → [{ title: 'Buy milk', done: true }, { title: 'Walk dog', done: false }]
 */
export function updateBy<T, K extends keyof T>(
  items: readonly T[],
  key: K,
  value: T[K],
  fn: (item: T) => T,
): readonly T[] {
  return updateWhere(items, (item) => item[key] === value, fn);
}

/**
 * Replace the item with the same `key` field as `item`; append it if none match
 * @example
 * const scores = [{ player: 'Ann', points: 10 }];
 * upsertBy(scores, 'player', { player: 'Ann', points: 15 });
 * // → [{ player: 'Ann', points: 15 }]
 * upsertBy(scores, 'player', { player: 'Bob', points: 7 });
 * // → [{ player: 'Ann', points: 10 }, { player: 'Bob', points: 7 }]
 */
export function upsertBy<T, K extends keyof T>(items: readonly T[], key: K, item: T): readonly T[] {
  return findBy(items, key, item[key])
    ? updateBy(items, key, item[key], () => item)
    : append(items, item);
}

/**
 * Remove every item matching a predicate
 * @example
 * removeWhere([1, 2, 3, 4], (n) => n % 2 === 0);
 * // → [1, 3]
 */
export function removeWhere<T>(
  items: readonly T[],
  predicate: (item: T, index: number) => boolean,
): readonly T[] {
  return items.filter((item, index) => !predicate(item, index));
}

/**
 * Remove every item whose `key` field equals `value`
 * @example
 * const cart = [{ sku: 'A1', qty: 2 }, { sku: 'B2', qty: 1 }];
 * removeBy(cart, 'sku', 'B2');
 * // → [{ sku: 'A1', qty: 2 }]
 */
export function removeBy<T, K extends keyof T>(
  items: readonly T[],
  key: K,
  value: T[K],
): readonly T[] {
  return removeWhere(items, (item) => item[key] === value);
}
