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

import type { ValidationReturn } from "@/types/types";
import { t } from "i18next";

interface NumberValidationOptions {
  min?: number;
  max?: number;
  integer?: boolean;
}

/**
 * Validates a number against specified numerical limits.
 *
 * @example
 * validateNumber(5, { min: 0, max: 10 }); // true
 * validateNumber(9, { min: 10, max: 20 }); // Error message
 *
 * @example <caption>With currying.</caption>
 * const fn = validateNumber({ min: 0, max: 10 });
 * fn(5); // true
 * fn(9); // Error message
 *
 * @param value - The number to validate.
 * @param [options] - Configuration options for validation.
 * @param [options.min=Number.MIN_SAFE_INTEGER] - Minimum allowed value.
 * @param [options.max=Number.MAX_SAFE_INTEGER] - Maximum allowed value.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validateNumber(value: number, options?: NumberValidationOptions): ValidationReturn;

export function validateNumber(
  options?: NumberValidationOptions,
): (value: number) => ValidationReturn;

export function validateNumber(
  valueOrOpts?: number | NumberValidationOptions,
  options: NumberValidationOptions = {},
): ValidationReturn | ((value: number) => ValidationReturn) {
  if (typeof valueOrOpts !== "number") {
    return (v: number) => validateNumber(v, valueOrOpts);
  }

  const value = valueOrOpts;

  if (!isFinite(value)) {
    return t("form.field.invalidNumber", { value });
  }

  const { min = Number.MIN_SAFE_INTEGER, max = Number.MAX_SAFE_INTEGER, integer = false } = options;

  if (integer && !Number.isInteger(valueOrOpts)) {
    return t("form.field.mustBeInteger");
  }

  if (value < min) {
    return t("form.field.minValue", { 0: min });
  }

  if (value > max) {
    return t("form.field.maxValue", { 0: max });
  }

  return true;
}
