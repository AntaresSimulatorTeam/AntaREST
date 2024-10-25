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

import { useMemo } from "react";
import { Item } from "@glideapps/glide-data-grid";
import { EnhancedGridColumn } from "../../core/types";
import { Column } from "../../core/constants";

/**
 * A custom hook that provides coordinate mapping functions for a grid with mixed column types.
 *
 * @description
 * This hook addresses a common issue in grid components that display both data and non-data columns:
 * the mismatch between grid coordinates (visual position) and data coordinates (position in the data array).
 *
 * The problem arises when a grid includes non-data columns (e.g., row headers, date/time columns)
 * alongside editable data columns. In such cases, the index of a column in the grid doesn't
 * directly correspond to its index in the data array. This can lead to issues where:
 * 1. The wrong data is displayed in cells.
 * 2. Edits are applied to incorrect data points.
 * 3. Non-editable columns are mistakenly treated as editable.
 *
 * This hook solves these issues by providing two mapping functions:
 * - gridToData: Converts grid coordinates to data array coordinates.
 * - dataToGrid: Converts data array coordinates to grid coordinates.
 *
 * By using these functions, components can ensure that they're always working with the correct
 * coordinates, whether they're displaying data, handling edits, or managing selection.
 *
 * @param columns - An array of column definitions, including their types.
 *
 * @returns An object containing two functions:
 *   - gridToData: (gridCoord: Item) => Item | null
 *     Converts grid coordinates to data coordinates. Returns null for non-data columns.
 *   - dataToGrid: (dataCoord: Item) => Item
 *     Converts data coordinates to grid coordinates.
 */
export function useColumnMapping(columns: EnhancedGridColumn[]) {
  return useMemo(() => {
    const dataColumnIndices = columns.reduce((acc, col, index) => {
      if (col.type === Column.Number) {
        acc.push(index);
      }
      return acc;
    }, [] as number[]);

    const gridToData = ([col, row]: Item): Item | null => {
      const dataColIndex = dataColumnIndices.indexOf(col);
      return dataColIndex !== -1 ? [dataColIndex, row] : null;
    };

    const dataToGrid = ([col, row]: Item): Item => [
      dataColumnIndices[col],
      row,
    ];

    return { gridToData, dataToGrid };
  }, [columns]);
}
