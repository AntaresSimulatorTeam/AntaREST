import { O } from "ts-toolbelt";

/**
 * Allow to use `any` with `Promise` type without disabling ESLint rule.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type PromiseAny = Promise<any>;

/**
 * Make all properties in T optional, except for those specified by K.
 */
export type PartialExceptFor<T, K extends keyof T> = O.Required<Partial<T>, K>;

export function tuple<T extends unknown[]>(...items: T): T {
  return items;
}
