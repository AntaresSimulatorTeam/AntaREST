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

import { v4 as uuidv4 } from "uuid";
import * as RA from "ramda-adjunct";

export function makeListItems<T>(
  value: readonly T[],
): Array<{ id: string; value: T }> {
  return value.map((v) => ({ id: uuidv4(), value: v }));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function makeLabel(value: any): string {
  // Default value for `getOptionLabel` prop in Autocomplete
  if (RA.isString(value?.label)) {
    return value.label;
  }
  return value?.toString() ?? "";
}
