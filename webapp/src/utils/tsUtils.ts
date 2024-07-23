import { O } from "ts-toolbelt";

/**
 * Allow to use `any` with `Promise` type without disabling ESLint rule.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type PromiseAny = Promise<any>;

/**
 * Allow to define an empty object.
 * Don't use `{}` as a type. `{}` actually means "any non-nullish value".
 */
export type EmptyObject = Record<string, never>;

/**
 * Make all properties in T optional, except for those specified by K.
 */
export type PartialExceptFor<T, K extends keyof T> = O.Required<Partial<T>, K>;

export function tuple<T extends unknown[]>(...items: T): T {
  return items;
}
