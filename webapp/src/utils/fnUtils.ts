/**
 * A utility function designed to be used as a placeholder or stub. It can be used in situations where you might
 * otherwise be tempted to disable an ESLint rule temporarily, such as when you need to pass a function that
 * does nothing (for example, as a default prop in React components or as a no-operation callback).
 *
 * By using this function, you maintain code cleanliness and intention clarity without directly suppressing
 * linting rules.
 *
 * @param args - Accepts any number of arguments of any type, but does nothing with them.
 */
export function voidFn<TArgs extends unknown[]>(...args: TArgs) {
  // Intentionally empty, as its purpose is to do nothing.
}
