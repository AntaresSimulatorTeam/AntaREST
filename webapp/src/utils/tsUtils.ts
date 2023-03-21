export function tuple<T extends unknown[]>(...items: T): T {
  return items;
}
