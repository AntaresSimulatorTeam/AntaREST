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
import { useEffect, useEffectEvent } from "react";
import type { EnhancedGridColumn } from "../shared/types";
import { parseClipboardNumber } from "../shared/utils";

interface UseMatrixPasteInterceptorOptions {
  readOnly: boolean;
  data: ReadonlyArray<readonly number[]>;
  columns: readonly EnhancedGridColumn[];
  visibleColumns: readonly EnhancedGridColumn[];
  visibleRows: number;
  filterActive: boolean;
  gridSelection: GridSelection;
  gridToData: (item: Item) => Item | null;
  getDataRowIndex: (visibleRow: number) => number;
  onBulkPaste?: (newData: number[][]) => void;
}

// Replaces glide-data-grid's built-in paste handling with a locale-aware.
//
// Two problems with the default behavior:
// 1. It reads `text/html` from the clipboard and walks the DOM to extract cells.
// On a large Excel paste (millions of cells) that can freeze the UI for several seconds.
//
// 2. Its async `Ctrl+V` keybinding uses `Number.parseFloat`, which mis-parses locale
// formats -> "4,567" becomes 4 instead of 4567.
//
// We disable glide's keybinding (`keybindings={{ paste: false }}` at the call site) and
// attach a capture-phase `window` listener so we fire before glide's own bubble-phase
// listener, call `stopImmediatePropagation()` to skip it, parse `text/plain` with
// locale-aware rules, and hand the fully-updated matrix to the caller in one shot.
export function useMatrixPasteInterceptor({
  readOnly,
  data,
  columns,
  visibleColumns,
  visibleRows,
  filterActive,
  gridSelection,
  gridToData,
  getDataRowIndex,
  onBulkPaste,
}: UseMatrixPasteInterceptorOptions) {
  const enabled = !readOnly && !!onBulkPaste;

  const handlePaste = useEffectEvent((e: ClipboardEvent) => {
    if (!onBulkPaste) {
      return;
    }

    const targetRange = gridSelection.current?.range;
    if (!targetRange) {
      return;
    }

    const text = e.clipboardData?.getData("text/plain") ?? "";
    if (!text) {
      return;
    }

    const pasteRows = parseTsv(text);
    if (pasteRows.length === 0) {
      return;
    }

    e.preventDefault();
    e.stopImmediatePropagation();

    const { x: startCol, y: startRow } = targetRange;

    const colMapping = buildColumnMapping({
      startCol,
      pasteColCount: pasteRows[0].length,
      columns,
      visibleColumns,
      filterActive,
      gridToData,
    });

    onBulkPaste(
      applyPasteToMatrix({
        data,
        pasteRows,
        colMapping,
        startRow,
        visibleRows,
        getDataRowIndex,
      }),
    );
  });

  useEffect(() => {
    if (!enabled) {
      return;
    }

    window.addEventListener("paste", handlePaste, { capture: true });
    return () => window.removeEventListener("paste", handlePaste, { capture: true });
    // `handlePaste` is a React 19 Effect Event (stable), intentionally omitted.
    // Can drop this disable once `eslint-plugin-react-hooks` is bumped to ≥ 7.1.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);
}

function parseTsv(text: string): string[][] {
  return text
    .split(/\r?\n/)
    .filter((row) => row.length > 0)
    .map((row) => row.split("\t"));
}

interface BuildColumnMappingOptions {
  startCol: number;
  pasteColCount: number;
  columns: readonly EnhancedGridColumn[];
  visibleColumns: readonly EnhancedGridColumn[];
  filterActive: boolean;
  gridToData: (item: Item) => Item | null;
}

// Pre-compute visible-col -> data-col index once (O(cols)) so the inner paste loop
// stays O(rows × cols) instead of degenerating to O(rows × cols × cols) lookups.
function buildColumnMapping({
  startCol,
  pasteColCount,
  columns,
  visibleColumns,
  filterActive,
  gridToData,
}: BuildColumnMappingOptions): Array<number | undefined> {
  // When the filter is active, `visibleColumns` is a subset of `columns`. Build a lookup
  // once so each paste column resolves to its original index in O(1).
  const idToOriginalCol = filterActive ? new Map(columns.map((col, i) => [col.id, i])) : null;

  const mapping = new Array<number | undefined>(pasteColCount);
  for (let colOffset = 0; colOffset < pasteColCount; colOffset++) {
    const visibleCol = startCol + colOffset;

    if (visibleCol >= visibleColumns.length) {
      continue;
    }

    const originalCol = idToOriginalCol
      ? (idToOriginalCol.get(visibleColumns[visibleCol].id) ?? -1)
      : visibleCol;

    if (originalCol < 0 || originalCol >= columns.length) {
      continue;
    }

    mapping[colOffset] = gridToData([originalCol, 0])?.[0];
  }

  return mapping;
}

interface ApplyPasteToMatrixOptions {
  data: ReadonlyArray<readonly number[]>;
  pasteRows: string[][];
  colMapping: Array<number | undefined>;
  startRow: number;
  visibleRows: number;
  getDataRowIndex: (visibleRow: number) => number;
}

function applyPasteToMatrix({
  data,
  pasteRows,
  colMapping,
  startRow,
  visibleRows,
  getDataRowIndex,
}: ApplyPasteToMatrixOptions): number[][] {
  const updatedData = data.map((row) => row.slice());
  const dataRowCount = updatedData.length;
  const dataColCount = updatedData[0]?.length ?? 0;

  for (let rowOffset = 0; rowOffset < pasteRows.length; rowOffset++) {
    const visibleRow = startRow + rowOffset;

    if (visibleRow >= visibleRows) {
      break;
    }

    const dataRow = getDataRowIndex(visibleRow);

    if (dataRow >= dataRowCount) {
      break;
    }

    const pasteRow = pasteRows[rowOffset];

    for (let colOffset = 0; colOffset < pasteRow.length; colOffset++) {
      const dataCol = colMapping[colOffset];

      if (dataCol === undefined || dataCol >= dataColCount) {
        continue;
      }

      const num = parseClipboardNumber(pasteRow[colOffset]);

      if (Number.isNaN(num)) {
        continue;
      }

      updatedData[dataRow][dataCol] = num;
    }
  }

  return updatedData;
}
