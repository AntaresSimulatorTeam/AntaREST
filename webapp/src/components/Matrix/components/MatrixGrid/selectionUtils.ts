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

import { CompactSelection, type GridSelection, type Rectangle } from "@glideapps/glide-data-grid";
import { Column } from "../../shared/constants";
import type { EnhancedGridColumn } from "../../shared/types";

export const EMPTY_SELECTION: GridSelection = {
  rows: CompactSelection.empty(),
  columns: CompactSelection.empty(),
};

interface NormalizeSelectionParams {
  selection: GridSelection;
  previous: GridSelection;
  columns: readonly EnhancedGridColumn[];
  rows: number;
}

/**
 * Keep aggregate selections within one column, independently of the input data.
 *
 * @param params - Selection and visible grid layout.
 * @param params.selection - Selection requested by Glide.
 * @param params.previous - Last accepted selection, used to identify newly selected columns.
 * @param params.columns - Visible columns in display order.
 * @param params.rows - Number of visible rows.
 * @returns The selection shared by the grid and its footer.
 */
export function normalizeSelection({
  selection,
  previous,
  columns,
  rows,
}: NormalizeSelectionParams): GridSelection {
  const isAggregate = (col: number) => columns[col]?.type === Column.Aggregate;

  if (!columns.some(({ type }) => type === Column.Aggregate)) {
    return selection;
  }

  if (selection.rows.length > 0) {
    return { ...EMPTY_SELECTION, rows: selection.rows };
  }

  if (selection.columns.length > 0) {
    const selected = [...selection.columns].filter((col) => columns[col] !== undefined);
    const added = selected.filter((col) => !previous.columns.hasIndex(col));
    // Shift-click adds an interval: its outer edge is the new selection target.
    const target = added[0] < (previous.columns.first() ?? -1) ? added[0] : added.at(-1);
    const aggregate =
      target !== undefined
        ? isAggregate(target)
          ? target
          : undefined
        : selected.find(isAggregate);

    return {
      ...EMPTY_SELECTION,
      columns:
        aggregate !== undefined
          ? CompactSelection.fromSingleSelection(aggregate)
          : selected.reduce(
              (result, col) => (isAggregate(col) ? result : result.add(col)),
              CompactSelection.empty(),
            ),
    };
  }

  if (!selection.current || rows === 0 || columns.length === 0) {
    return EMPTY_SELECTION;
  }

  const { cell, range, rangeStack } = selection.current;
  let firstCol = 0;
  let lastCol = columns.length - 1;
  const focusedCol = Math.min(lastCol, Math.max(0, cell[0]));

  // Use the anchor for every range, including full-grid drags and Select All.
  if (isAggregate(focusedCol)) {
    firstCol = focusedCol;
    lastCol = focusedCol;
  } else {
    // Clamp drag and keyboard extensions at the nearest aggregate boundary.
    for (let col = focusedCol - 1; col >= 0; col--) {
      if (isAggregate(col)) {
        firstCol = col + 1;
        break;
      }
    }
    for (let col = focusedCol + 1; col < columns.length; col++) {
      if (isAggregate(col)) {
        lastCol = col - 1;
        break;
      }
    }
  }

  const constrainRange = ({ x, y, width, height }: Rectangle): Rectangle => {
    const left = Math.max(firstCol, x);
    const top = Math.max(0, y);
    return {
      x: left,
      y: top,
      width: Math.min(lastCol + 1, x + width) - left,
      height: Math.min(rows, y + height) - top,
    };
  };

  const constrained = constrainRange(range);

  if (constrained.width <= 0 || constrained.height <= 0) {
    return EMPTY_SELECTION;
  }

  return {
    ...EMPTY_SELECTION,
    current: {
      cell: [
        focusedCol,
        Math.max(constrained.y, Math.min(constrained.y + constrained.height - 1, cell[1])),
      ],
      range: constrained,
      rangeStack: rangeStack
        .map(constrainRange)
        .filter(({ width, height }) => width > 0 && height > 0),
    },
  };
}
