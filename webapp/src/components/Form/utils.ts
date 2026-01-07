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

import { toError } from "@/utils/fnUtils";
import axios from "axios";
import isMatchWith from "lodash/isMatchWith";
import * as RA from "ramda-adjunct";
import type { FieldValues } from "react-hook-form";

// Any error under the `root` key are not persisted with each submission.
// They will be deleted automatically.
// cf. https://www.react-hook-form.com/api/useform/seterror/
export const ROOT_FETCH_ERROR_KEY = "fetchError";
export const ROOT_SUBMIT_ERROR_KEY = "submitError";

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

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const description = error.response?.data?.description;
    if (description) {
      return description;
    }
  }

  return toError(error).message;
}
