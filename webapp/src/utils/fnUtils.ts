/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

/**
 * A utility function that converts an unknown value to an Error object.
 * If the value is already an Error object, it is returned as is.
 * If the value is a string, it is used as the message for the new Error object.
 * If the value is anything else, a new Error object with a generic message is created.
 *
 * @param error - The value to convert to an Error object.
 * @returns An Error object.
 */
export function toError(error: unknown) {
  if (error instanceof Error) {
    return error;
  }
  if (typeof error === "string") {
    return new Error(error);
  }
  return new Error("An unknown error occurred");
}
