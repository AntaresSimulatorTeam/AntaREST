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

import isMatchWith from "lodash/isMatchWith";
import * as RA from "ramda-adjunct";
import type { FieldValues } from "react-hook-form";

// From https://github.com/react-hook-form/react-hook-form/blob/master/src/utils/stringToPath.ts
export function stringToPath(input: string): string[] {
  return input
    .replace(/["|']|\]/g, "")
    .split(/\.|\[/)
    .filter(Boolean);
}

/**
 * Performs a deep comparison between `object` and `source` to determine if `source` shape
 * is present in object.
 *
 * Note: The function MUST be replaced with Zod schema validation in the future.
 *
 * @param object - The object to inspect.
 * @param source - The object of property values to match.
 * @returns `true` if object is a match, else `false`.
 */
export function isMatch<T extends FieldValues>(object: unknown, source: T): object is T {
  if (!RA.isPlainObj(object)) {
    return false;
  }

  return isMatchWith(object, source, (objValue, srcValue) => {
    if (RA.isPlainObj(objValue) && RA.isPlainObj(srcValue)) {
      return isMatch(objValue, srcValue);
    }

    return typeof objValue === typeof srcValue;
  });
}

export const ROOT_ERROR_KEY = "default";
