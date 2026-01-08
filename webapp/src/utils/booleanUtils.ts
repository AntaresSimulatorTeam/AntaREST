/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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
 * Converts a boolean value to its string representation (`"true"` or `"false"`).
 *
 * Unlike the native `Boolean.prototype.toString()` method, this function returns the exact
 * string literals types `"true"` or `"false"` (not just `string`), preserving strict typing.
 *
 * @param value - The boolean value to convert.
 * @returns `"true"` if the value is `true`, `"false"` if the value is `false`.
 */
export function booleanToString(value: boolean) {
  return value ? "true" : "false";
}

/**
 * Converts a string representation of a boolean (`"true"` or `"false"`)
 * to its appropriate boolean value.
 *
 * If the input is not a valid string representation of a boolean,
 * the provided default value is returned.
 *
 * @param value - The string value to convert.
 * @param defaultValue - The default value to return if the input is not a valid
 * string representation of a boolean.
 * @returns `true` if the value is `"true"`, `false` if the value is `"false"`,
 * or the provided default value otherwise.
 */
export function stringToBoolean(value: string, defaultValue = false) {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return defaultValue;
}

/**
 * Checks if a string is a valid boolean representation (`"true"` or `"false"`).
 *
 * @param value - The string value to check.
 * @returns `true` if the value is `"true"` or `"false"`, `false` otherwise.
 */
export function isBooleanString(value: string): value is "true" | "false" {
  return value === "true" || value === "false";
}
