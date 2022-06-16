export function isDependencyList(
  value: unknown
): value is React.DependencyList {
  return Array.isArray(value);
}
