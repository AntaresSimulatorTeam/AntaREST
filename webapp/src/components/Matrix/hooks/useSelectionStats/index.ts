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
  /**
   * Resolves visible grid coordinates to an unrounded numeric value.
   * Returns undefined for cells excluded from statistics.
   *
   * Its identity must change when underlying values change so the memoized
   * statistics are recalculated, even when the selection stays unchanged.
   */
  getCellValue: (coordinates: Item) => number | undefined;
}

/**
 * Calculates footer statistics using visible grid coordinates.
 *
 * Overlapping cell ranges contribute each cell once. Row selections include
 * only matrix inputs, column selections can also summarize aggregate values.
 *
 * @param params - Selection, visible grid layout, and value lookup.
 * @param params.selection - Grid selection to summarize.
 * @param params.columns - Visible columns in display order.
 * @param params.rows - Number of visible rows.
 * @param params.getCellValue - Resolves visible cells to their unrounded numeric values.
 * @returns Statistics, or null when the selection contains no numeric values.
 */
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
      // Clip once per rectangle. right and bottom are exclusive bounds.
      const left = Math.max(0, range.x);
      const right = Math.min(columns.length, range.x + range.width);
      const top = Math.max(0, range.y);
      const bottom = Math.min(rows, range.y + range.height);
      const earlierRanges = ranges.slice(0, index);

      for (let col = left; col < right; col++) {
        for (let row = top; row < bottom; row++) {
          // Only earlier ranges have contributed cells. Skip their overlaps to count each cell once.
          const alreadySelected =
            index > 0 &&
            earlierRanges.some(
              ({ x, y, width, height }) =>
                col >= x && col < x + width && row >= y && row < y + height,
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
