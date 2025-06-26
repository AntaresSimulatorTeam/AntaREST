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

/**
 * Combines multiple validation functions into a single function.
 * Each validator is called in sequence, and the first one that returns
 * an error message will stop the validation process.
 *
 * @param validators - An array of validation functions.
 * @returns A single validation function.
 */
export function combineValidators<T>(
  ...validators: Array<(value: T) => ValidationReturn>
): (value: T) => ValidationReturn {
  return (value: T): ValidationReturn => {
    for (const validator of validators) {
      const result = validator(value);
      if (result !== true) {
        return result;
      }
    }
    return true;
  };
}
