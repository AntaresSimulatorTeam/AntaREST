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

import DataGrid, { type DataGridHandle } from "@/components/DataGrid";
import {
  CompactSelection,
  GridCellKind,
  type EditableGridCell,
  type EditListItem,
  type GridKeyEventArgs,
  type GridSelection,
  type Item,
} from "@glideapps/glide-data-grid";
import { useCallback, useContext, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { MatrixContext } from "../../context/MatrixContext";
import { useColumnMapping } from "../../hooks/useColumnMapping";
import { useGridCellContent } from "../../hooks/useGridCellContent";
import { useMatrixPasteInterceptor } from "../../hooks/useMatrixPasteInterceptor";
import { useSelectionStats } from "../../hooks/useSelectionStats";
import { Column } from "../../shared/constants";
import type {
  AggregateType,
  DateTimes,
  EnhancedGridColumn,
  GridUpdate,
  MatrixAggregates,
  NonEmptyMatrix,
} from "../../shared/types";
import { calculateMatrixAggregates, formatGridNumber } from "../../shared/utils";
import MatrixStats from "../MatrixStats";

// Fonts match baseFontStyle / headerFontStyle + fontFamily from Matrix/styles.ts.
const CELL_FONT = "13px Inter, sans-serif";
const HEADER_FONT = "bold 11px Inter, sans-serif";
// 2 × cellHorizontalPadding (8 px each side) + 4 px safety margin.
const CELL_CONTENT_PADDING = 20;

let _canvas: HTMLCanvasElement | null = null;

function measureTextWidth(text: string, font: string): number {
  _canvas ??= document.createElement("canvas");
  const ctx = _canvas.getContext("2d");

  if (!ctx) {
    return 0;
  }

  ctx.font = font;
  return ctx.measureText(text).width;
}

// Computes which columns need to grow to fit the pasted content.
// Handles both data (Column.Number) and aggregate (Column.Aggregate) columns.
function computeColumnWidths(
  newData: number[][],
  columns: readonly EnhancedGridColumn[],
  gridToData: (item: Item) => Item | null,
): Map<string, number> {
  const updates = new Map<string, number>();

  const aggregateTypes = columns
    .filter((col) => col.type === Column.Aggregate)
    .map((col) => col.id as AggregateType);

  const aggregates =
    aggregateTypes.length > 0
      ? calculateMatrixAggregates({ matrix: newData, types: aggregateTypes })
      : null;

  for (let colIdx = 0; colIdx < columns.length; colIdx++) {
    const col = columns[colIdx];
    let values: number[];
    let maxDecimals: number;

    if (col.type === Column.Number) {
      const mapped = gridToData([colIdx, 0]);
      if (mapped === null) {
        continue;
      }
      const dataCol = mapped[0];
      if (dataCol >= (newData[0]?.length ?? 0)) {
        continue;
      }
      values = newData.map((row) => row[dataCol]);
      maxDecimals = 6;
    } else if (col.type === Column.Aggregate && aggregates) {
      values = aggregates[col.id as keyof MatrixAggregates] ?? [];
      maxDecimals = 3;
    } else {
      continue;
    }

    let maxContentWidth = 0;
    for (const value of values) {
      if (!Number.isFinite(value)) {
        continue;
      }

      const display = formatGridNumber({ value, maxDecimals });
      maxContentWidth = Math.max(maxContentWidth, measureTextWidth(display, CELL_FONT));
    }

    if (maxContentWidth === 0) {
      continue;
    }

    const neededWidth = Math.ceil(maxContentWidth) + CELL_CONTENT_PADDING;
    // For auto-sized columns use header text width as effective current width so we
    // only grow, never shrink, a column whose header is already wider.
    const effectiveCurrentWidth =
      col.width ?? Math.ceil(measureTextWidth(col.title, HEADER_FONT)) + CELL_CONTENT_PADDING;

    if (neededWidth > effectiveCurrentWidth) {
      updates.set(col.id, neededWidth);
    }
  }

  return updates;
}

export interface MatrixGridProps {
  data: NonEmptyMatrix;
  rows: number;
  columns: readonly EnhancedGridColumn[];
  dateTime?: DateTimes;
  aggregates?: Partial<MatrixAggregates>;
  rowHeaders?: string[];
  width?: string;
  height?: string;
  onCellEdit?: (update: GridUpdate) => void;
  onMultipleCellsEdit?: (updates: GridUpdate[]) => void;
  /**
   * Called on paste with the full updated matrix (same shape as `data`). Omit this prop
   * to make paste a no-op (e.g. for read-only standalone usage).
   */
  onBulkPaste?: (newData: number[][]) => void;
  readOnly?: boolean;
  showPercent?: boolean;
  showStats?: boolean;
}

function MatrixGrid({
  data,
  rows,
  columns,
  dateTime,
  aggregates,
  rowHeaders,
  width = "100%",
  height = "100%",
  onCellEdit,
  onMultipleCellsEdit,
  onBulkPaste,
  readOnly,
  showPercent,
  showStats = true,
}: MatrixGridProps) {
  const { t } = useTranslation();

  // MatrixContext is optional to support standalone usage of MatrixGrid.
  // When used within Matrix component, context provides filter preview functionality.
  // When used standalone, we provide sensible defaults (no filtering).
  const context = useContext(MatrixContext);

  // If no context is available (standalone usage), create default filter preview
  // that shows all rows and columns (no filtering applied)
  const filterPreview = context?.filterPreview ?? {
    active: false, // Filtering is disabled in standalone mode
    criteria: {
      columnsIndices: Array.from({ length: data[0]?.length || 0 }, (_, i) => i),
      rowsIndices: Array.from({ length: rows }, (_, i) => i),
    },
  };

  const [gridSelection, setGridSelection] = useState<GridSelection>({
    rows: CompactSelection.empty(),
    columns: CompactSelection.empty(),
  });

  // For filter preview mode, we need to map visible rows to data rows
  const { rowsIndices, columnsIndices } = useMemo(() => {
    if (!filterPreview.active) {
      return {
        // When no filter is active, all rows and columns are visible
        rowsIndices: Array.from({ length: rows }, (_, i) => i),
        columnsIndices: Array.from({ length: data[0]?.length || 0 }, (_, i) => i),
      };
    }

    return filterPreview.criteria;
  }, [data, rows, filterPreview.active, filterPreview.criteria]);

  // Filter to identify which columns in the grid are data columns (numbers editable)
  const dataColumnIndices = useMemo(() => {
    return columns
      .map((col, idx) => (col.type === Column.Number ? idx : null))
      .filter((idx): idx is number => idx !== null);
  }, [columns]);

  // Filter columns for preview mode - only filter data columns, keep non-data columns
  const visibleColumns = useMemo(() => {
    if (!filterPreview.active) {
      return columns;
    }

    return columns.filter((column, idx) => {
      // Keep non-data columns (datetime, text, aggregates)
      if (column.type !== Column.Number) {
        return true;
      }

      // For data columns, check if they should be visible
      const dataColIndex = dataColumnIndices.indexOf(idx);
      return dataColIndex === -1 || columnsIndices.includes(dataColIndex);
    });
  }, [columns, filterPreview.active, dataColumnIndices, columnsIndices]);

  const visibleRows = rowsIndices.length;

  const getDataRowIndex = useCallback(
    (visibleRowIndex: number): number => {
      return filterPreview.active
        ? (rowsIndices[visibleRowIndex] ?? visibleRowIndex)
        : visibleRowIndex;
    },
    [filterPreview.active, rowsIndices],
  );

  const { gridToData } = useColumnMapping(columns);

  const originalGetCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
    readOnly || filterPreview.active,
    showPercent,
  );

  const getCellContent = useCallback(
    (cell: Item): ReturnType<ReturnType<typeof useGridCellContent>> => {
      // Map the visible row to the actual data row
      const [visibleCol, visibleRow] = cell;
      const dataRow = getDataRowIndex(visibleRow);

      // When in preview mode, we need to map the visible column index to the original column index
      let originalCol = visibleCol;

      if (filterPreview.active) {
        // Check if the column index is within bounds
        if (visibleCol >= 0 && visibleCol < visibleColumns.length) {
          const foundIndex = columns.findIndex((col) => col.id === visibleColumns[visibleCol].id);
          // Only use the found index if it's valid (not -1)
          originalCol = foundIndex !== -1 ? foundIndex : visibleCol;
        } else {
          // If out of bounds, pass the original column index which will be handled by useGridCellContent
          originalCol = visibleCol;
        }
      }

      const mappedCell: Item = [originalCol, dataRow];

      return originalGetCellContent(mappedCell);
    },
    [getDataRowIndex, originalGetCellContent, filterPreview.active, columns, visibleColumns],
  );

  // When filters are active, use filtered data for stats calculation
  const filteredData = filterPreview.active
    ? rowsIndices.map((rowIndex) =>
        columnsIndices.map((colIndex) => data[rowIndex]?.[colIndex] ?? 0),
      )
    : data;

  const selectionStats = useSelectionStats({
    data: filteredData,
    selection: gridSelection,
    gridToData,
  });

  const dataGridRef = useRef<DataGridHandle>(null);

  const handleBulkPaste = useCallback(
    (newData: number[][]) => {
      onBulkPaste?.(newData);
      const updates = computeColumnWidths(newData, columns, gridToData);
      if (updates.size > 0) {
        dataGridRef.current?.resizeColumns(updates);
      }
    },
    [onBulkPaste, columns, gridToData],
  );

  useMatrixPasteInterceptor({
    readOnly: !!readOnly,
    data,
    columns,
    visibleColumns,
    visibleRows,
    filterActive: filterPreview.active,
    gridSelection,
    gridToData,
    getDataRowIndex,
    onBulkPaste: onBulkPaste ? handleBulkPaste : undefined,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellEdited = (coordinates: Item, value: EditableGridCell) => {
    if (value.kind !== GridCellKind.Number) {
      // Invalid numeric value
      return;
    }

    // Map visible row to data row for editing
    const [visibleCol, visibleRow] = coordinates;
    const dataRow = getDataRowIndex(visibleRow);

    // When in preview mode, we need to map the visible column index to the original column index
    const originalCol = filterPreview.active
      ? columns.findIndex((col) => col.id === visibleColumns[visibleCol].id)
      : visibleCol;

    const mappedCoordinates: Item = [originalCol, dataRow];
    const dataCoordinates = gridToData(mappedCoordinates);

    if (dataCoordinates && onCellEdit) {
      onCellEdit({ coordinates: dataCoordinates, value });
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit): GridUpdate | null => {
        // Map visible row to data row for batch edits
        const [visibleCol, visibleRow] = edit.location;
        const dataRow = getDataRowIndex(visibleRow);

        // When in preview mode, we need to map the visible column index to the original column index
        const originalCol = filterPreview.active
          ? columns.findIndex((col) => col.id === visibleColumns[visibleCol].id)
          : visibleCol;

        const mappedLocation: Item = [originalCol, dataRow];
        const dataCoordinates = gridToData(mappedLocation);

        if (edit.value.kind !== GridCellKind.Number || !dataCoordinates) {
          return null;
        }

        return {
          coordinates: dataCoordinates,
          value: edit.value,
        };
      })
      .filter((update): update is GridUpdate => update !== null);

    if (updates.length === 0) {
      // No valid updates
      return;
    }

    if (onCellEdit && updates.length === 1) {
      // If only one cell is edited,`onCellEdit` is called
      // we don't need to call `onMultipleCellsEdit`
      return;
    }

    if (onMultipleCellsEdit) {
      onMultipleCellsEdit(updates);
    }

    // Return true to prevent calling `onCellEdit`
    // for each cell after`onMultipleCellsEdit` is called
    return true;
  };

  const handleKeyDown = useCallback(
    (event: GridKeyEventArgs) => {
      // Fill selection with value (Ctrl+Shift+Enter)
      if (event.shiftKey && event.ctrlKey && event.key === "Enter") {
        if (
          gridSelection.current?.range ||
          gridSelection.rows.length > 0 ||
          gridSelection.columns.length > 0
        ) {
          const userInput = prompt(t("matrix.fillSelection.numberPrompt"));

          // Return early if user cancelled or input is empty/whitespace
          if (userInput === null || userInput.trim() === "") {
            return;
          }

          const value = Number(userInput);

          if (Number.isNaN(value)) {
            alert(t("form.field.invalidValue"));
            return;
          }

          const updates: GridUpdate[] = [];

          const addItemUpdate = (item: Item) => {
            const [visibleCol, visibleRow] = item;
            const dataRow = getDataRowIndex(visibleRow);

            // When in preview mode, we need to map the visible column index to the original column index
            let originalCol = visibleCol;
            let column = columns[originalCol];

            if (filterPreview.active && visibleCol >= 0 && visibleCol < visibleColumns.length) {
              const foundIndex = columns.findIndex(
                (col) => col.id === visibleColumns[visibleCol].id,
              );
              if (foundIndex !== -1) {
                originalCol = foundIndex;
                column = visibleColumns[visibleCol];
              }
            }

            const mappedItem: Item = [originalCol, dataRow];

            if (!column.editable || column.type !== GridCellKind.Number) {
              return;
            }

            const coordinates = gridToData(mappedItem);

            if (coordinates) {
              updates.push({
                coordinates,
                value: {
                  kind: GridCellKind.Number,
                  data: value,
                  displayData: formatGridNumber({ value }),
                  allowOverlay: true,
                },
              });
            }
          };

          // Handle range selection
          if (gridSelection.current?.range) {
            const { x, y, width, height } = gridSelection.current.range;

            for (let col = x; col < x + width; col++) {
              for (let row = y; row < y + height; row++) {
                addItemUpdate([col, row]);
              }
            }
          }

          // Handle row selections
          else if (gridSelection.rows.length > 0) {
            for (const rowIndex of gridSelection.rows) {
              for (let col = 0; col < visibleColumns.length; col++) {
                addItemUpdate([col, rowIndex]);
              }
            }
          }

          // Handle column selections
          else if (gridSelection.columns.length > 0) {
            for (const colIndex of gridSelection.columns) {
              for (let row = 0; row < visibleRows; row++) {
                addItemUpdate([colIndex, row]);
              }
            }
          }

          // Apply the updates if there are any
          if (updates.length > 0 && onMultipleCellsEdit) {
            onMultipleCellsEdit(updates);
          }
        }
      }
    },
    [
      gridSelection,
      gridToData,
      onMultipleCellsEdit,
      columns,
      visibleColumns,
      filterPreview.active,
      visibleRows,
      t,
      getDataRowIndex,
    ],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <DataGrid
        ref={dataGridRef}
        key={`matrix-grid-${columns.length}-${data.length}`}
        width={width}
        height={height}
        rows={visibleRows}
        columns={visibleColumns}
        getCellContent={getCellContent}
        onCellEdited={handleCellEdited}
        onCellsEdited={handleCellsEdited}
        getCellsForSelection
        // Disable glide-data-grid's own Ctrl+V handler: its async `Number.parseFloat` path
        // races our locale-aware capture-phase listener and wins the last write, corrupting
        // thousand-separator values like "4,567" into 4.
        keybindings={{ paste: false }}
        fillHandle={!readOnly}
        onKeyDown={readOnly ? undefined : handleKeyDown}
        allowedFillDirections="any"
        rowMarkers="both"
        freezeColumns={1} // Make the first column sticky
        cellActivationBehavior="second-click"
        onGridSelectionChange={setGridSelection}
        readOnly={readOnly}
      />
      {showStats && <MatrixStats stats={selectionStats} />}
    </>
  );
}

export default MatrixGrid;
