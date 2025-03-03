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
import * as R from "ramda";

interface ArrayValidationOptions {
  allowEmpty?: boolean;
  allowDuplicate?: boolean;
}

/**
 * Validates an array against specified criteria.
 * This function checks for duplicate values in the array.
 *
 * @example
 * validateArray([1, 2, 3], { allowDuplicate: false }); // true
 * validateArray([1, 1, 2, 3], { allowDuplicate: false }); // Error message
 *
 * @example <caption>With currying.</caption>
 * const fn = validateArray({ allowDuplicate: false });
 * fn([1, 2, 3]); // true
 * fn([1, 1, 2, 3]); // Error message
 *
 * @param value - The array to validate.
 * @param [options] - Configuration options for validation.
 * @param [options.allowEmpty=false] - Sets whether empty array is allowed or not.
 * @param [options.allowDuplicate=false] - Sets whether duplicate values are allowed or not.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validateArray<T>(value: T[], options?: ArrayValidationOptions): ValidationReturn;

export function validateArray<T>(
  options?: ArrayValidationOptions,
): (value: T[]) => ValidationReturn;

export function validateArray<T>(
  valueOrOpts?: T[] | ArrayValidationOptions,
  options: ArrayValidationOptions = {},
): ValidationReturn | ((value: T[]) => ValidationReturn) {
  if (!Array.isArray(valueOrOpts)) {
    return (v: T[]) => validateArray(v, valueOrOpts);
  }

  const value = valueOrOpts;
  const { allowEmpty, allowDuplicate } = options;

  if (!value.length && !allowEmpty) {
    return t("form.field.required");
  }

  if (!allowDuplicate && R.uniq(value).length !== value.length) {
    return t("form.field.duplicateNotAllowed");
  }

  return true;
}
