/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { L, O } from "ts-toolbelt";

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

/**
 * Check if a value is included in a list with type inference.
 *
 * @param value - The value to check.
 * @param list - The list to check against.
 * @returns `true` if the value is included in the list, `false` otherwise.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function includes<T, U extends any[]>(value: T, list: U): value is L.UnionOf<U> {
  return list.includes(value);
}
