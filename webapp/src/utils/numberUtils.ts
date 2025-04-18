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

/**
 * Checks if a string value is a valid numeric representation that can be parsed.
 *
 * @param value - The value to check
 * @returns true if the value can be converted to a valid number, false otherwise
 */
export function isNumericValue(value: unknown) {
  if (typeof value === "number") {
    return !Number.isNaN(value);
  }

  if (typeof value !== "string") {
    return false;
  }

  if (value.trim() === "") {
    return false;
  }

  const num = Number(value);
  return !Number.isNaN(num);
}
