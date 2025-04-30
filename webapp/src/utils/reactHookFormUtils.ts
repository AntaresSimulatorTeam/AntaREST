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

import * as R from "ramda";

////////////////////////////////////////////////////////////////
// `setValueAs` Register Option
////////////////////////////////////////////////////////////////

type NumericValue = number | string;

interface NumberOptions {
  min?: number;
  max?: number;
}

/**
 * Converts a numeric value to a number, clamping it within specified limits.
 *
 * @example
 * setValueAsNumber("5", { min: 0, max: 10 }); // 5
 * setValueAsNumber(11, { min: 0, max: 10 }); // 10
 *
 * @example <caption>With currying.</caption>
 * const fn = setValueAsNumber({ min: 0, max: 10 });
 * fn(5); // 5
 * fn(11); // 10
 *
 * @param value - The numeric value to convert.
 * @param options - Configuration options for conversion.
 * @param [options.min=Number.MIN_SAFE_INTEGER] - Minimum allowed value.
 * @param [options.max=Number.MAX_SAFE_INTEGER] - Maximum allowed value.
 * @returns The converted number, clamped within the specified limits.
 */
export function setValueAsNumber(value: NumericValue, options?: NumberOptions): number;

export function setValueAsNumber(options?: NumberOptions): (value: NumericValue) => number;

export function setValueAsNumber(
  valueOrOpts?: NumericValue | NumberOptions,
  options: NumberOptions = {},
): NumericValue | ((value: NumericValue) => number) {
  if (typeof valueOrOpts !== "number" && typeof valueOrOpts !== "string") {
    return (v: NumericValue) => setValueAsNumber(v, valueOrOpts);
  }

  const value = valueOrOpts;
  const { min = Number.MIN_SAFE_INTEGER, max = Number.MAX_SAFE_INTEGER } = options;

  // Returning empty string allow empty the field with backspace
  // and allow to write a negative number
  return value === "" ? "" : R.clamp(min, max, Number(value));
}
