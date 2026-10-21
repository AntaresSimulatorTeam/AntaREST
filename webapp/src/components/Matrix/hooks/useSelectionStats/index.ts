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

import type { GridSelection, Item } from "@glideapps/glide-data-grid";
import { useMemo } from "react";
import { Column } from "../../shared/constants";
import type { EnhancedGridColumn } from "../../shared/types";

export interface SelectionStats {
  sum: number;
  average: number;
  min: number;
  max: number;
  count: number;
}

interface UseSelectionStatsProps {
  selection: GridSelection;
  columns: readonly EnhancedGridColumn[];
  rows: number;
  getCellValue: (coordinates: Item) => number | undefined;
}

export function useSelectionStats({
  selection,
  columns,
  rows,
  getCellValue,
}: UseSelectionStatsProps): SelectionStats | null {
  return useMemo(() => {
    let sum = 0;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    let count = 0;

    const processCell = (col: number, row: number) => {
      const value = getCellValue([col, row]);

      if (value !== undefined) {
        sum += value;
        min = Math.min(min, value);
        max = Math.max(max, value);
        count++;
      }
    };

    // Include ranges retained by multi-rect selection or keyboard navigation, even in rect mode.
    const ranges = selection.current
      ? [...selection.current.rangeStack, selection.current.range]
      : [];

    for (const [index, range] of ranges.entries()) {
      // Clip each rectangle to the visible grid before reading cell values.
      for (
        let col = Math.max(0, range.x);
        col < Math.min(columns.length, range.x + range.width);
        col++
      ) {
        for (let row = Math.max(0, range.y); row < Math.min(rows, range.y + range.height); row++) {
          // Earlier ranges already contributed their cells, skip overlaps to count each cell once.
          const alreadySelected =
            index > 0 &&
            ranges.some(
              ({ x, y, width, height }, previousIndex) =>
                previousIndex < index &&
                col >= x &&
                col < x + width &&
                row >= y &&
                row < y + height,
            );

          if (!alreadySelected) {
            processCell(col, row);
          }
        }
      }
    }

    for (const row of selection.rows) {
      if (row < 0 || row >= rows) {
        continue;
      }

      for (const [col, column] of columns.entries()) {
        // Row selection summarizes matrix inputs, not their derived aggregates.
        if (column.type === Column.Number) {
          processCell(col, row);
        }
      }
    }

    // A selected column contributes all visible rows, including aggregates when selected.
    for (const col of selection.columns) {
      if (col < 0 || col >= columns.length) {
        continue;
      }

      for (let row = 0; row < rows; row++) {
        processCell(col, row);
      }
    }

    return count ? { sum, min, max, count, average: sum / count } : null;
  }, [selection, columns, rows, getCellValue]);
}
