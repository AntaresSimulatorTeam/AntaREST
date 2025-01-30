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

import type { GridColumn } from "@glideapps/glide-data-grid";
import { measureTextWidth } from "./domUtils";

/**
 * Gets the width of the given column.
 *
 * @param column - The column to get the width of.
 * @param values - The values of the column.
 * @returns The width of the column.
 */
export function getColumnWidth(column: GridColumn, values: () => string[]) {
  if ("width" in column) {
    return column.width;
  }

  const width = Math.max(
    measureTextWidth(column.title),
    // `values` is a function to prevent unnecessary computation if the column already has a width
    ...values().map((value) => measureTextWidth(value)),
  );

  // Under 110px, add a margin to the width to prevent text from being cut off
  return width < 110 ? width + 15 : width;
}
