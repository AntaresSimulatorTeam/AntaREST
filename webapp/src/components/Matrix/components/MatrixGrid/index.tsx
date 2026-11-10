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
  DateTimes,
  EnhancedGridColumn,
  GridUpdate,
  MatrixAggregates,
  NonEmptyMatrix,
} from "../../shared/types";
import { computeColumnWidths, formatGridNumber } from "../../shared/utils";
import MatrixStats from "../MatrixStats";
import { EMPTY_SELECTION, normalizeSelection } from "./selectionUtils";

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
  const [gridSelection, setGridSelection] = useState<GridSelection>(EMPTY_SELECTION);

  // Standalone grids have no context and display all rows and columns.
  const context = useContext(MatrixContext);
  const filterActive = context?.filterPreview.active ?? false;
  const filterCriteria = context?.filterPreview.active ? context.filterPreview.criteria : undefined;
  const dataColumnCount = data[0].length;

  const { rowsIndices, columnsIndices } = useMemo(
    () =>
      filterCriteria ?? {
        rowsIndices: Array.from({ length: rows }, (_, i) => i),
        columnsIndices: Array.from({ length: dataColumnCount }, (_, i) => i),
      },
    [rows, dataColumnCount, filterCriteria],
  );

  const { gridToData } = useColumnMapping(columns);

  // Filter columns for preview mode - only filter data columns, keep non-data columns
  const { visibleColumns, visibleColumnIndices } = useMemo(() => {
    if (!filterActive) {
      return { visibleColumns: columns, visibleColumnIndices: columns.map((_, col) => col) };
    }

    const selectedColumns = new Set(columnsIndices);
    const visibleColumnIndices: number[] = [];
    const visibleColumns = columns.filter((_, col) => {
      const dataCell = gridToData([col, 0]);
      const visible = dataCell === null || selectedColumns.has(dataCell[0]);
      if (visible) {
        visibleColumnIndices.push(col);
      }
      return visible;
    });

    return { visibleColumns, visibleColumnIndices };
  }, [columns, filterActive, gridToData, columnsIndices]);

  const visibleRows = rowsIndices.length;

  // Changing the visible layout invalidates the selection's grid coordinates.
  const selectionLayout = useMemo(
    () => JSON.stringify([visibleColumns.map(({ id }) => id), filterActive ? rowsIndices : rows]),
    [visibleColumns, filterActive, rowsIndices, rows],
  );

  const [previousSelectionLayout, setPreviousSelectionLayout] = useState(selectionLayout);

  // Reset before rendering children so the grid and footer never receive stale coordinates.
  if (previousSelectionLayout !== selectionLayout) {
    setPreviousSelectionLayout(selectionLayout);
    setGridSelection(EMPTY_SELECTION);
  }

  const handleGridSelectionChange = useCallback(
    (selection: GridSelection) => {
      setGridSelection((previous) =>
        normalizeSelection({ selection, previous, columns: visibleColumns, rows: visibleRows }),
      );
    },
    [visibleColumns, visibleRows],
  );

  const getDataRowIndex = useCallback(
    (visibleRowIndex: number) => {
      return filterActive ? (rowsIndices[visibleRowIndex] ?? visibleRowIndex) : visibleRowIndex;
    },
    [filterActive, rowsIndices],
  );

  const getOriginalCell = useCallback(
    ([col, row]: Item): Item => [visibleColumnIndices[col] ?? col, getDataRowIndex(row)],
    [visibleColumnIndices, getDataRowIndex],
  );

  const originalGetCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
    readOnly || filterActive,
    showPercent,
  );

  const getCellContent = useCallback(
    (cell: Item) => originalGetCellContent(getOriginalCell(cell)),
    [originalGetCellContent, getOriginalCell],
  );

  const getCellValue = useCallback(
    (cell: Item): number | undefined => {
      const originalCell = getOriginalCell(cell);
      const [col, row] = originalCell;
      const column = columns[col];

      if (column?.type === Column.Aggregate) {
        return aggregates?.[column.id as keyof MatrixAggregates]?.[row];
      }

      const coordinates = gridToData(originalCell);
      return coordinates ? data[coordinates[1]]?.[coordinates[0]] : undefined;
    },
    [getOriginalCell, columns, aggregates, gridToData, data],
  );

  const selectionStats = useSelectionStats({
    selection: gridSelection,
    columns: visibleColumns,
    rows: visibleRows,
    getCellValue,
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
    filterActive,
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

    const dataCoordinates = gridToData(getOriginalCell(coordinates));

    if (dataCoordinates && onCellEdit) {
      onCellEdit({ coordinates: dataCoordinates, value });
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit): GridUpdate | null => {
        const dataCoordinates = gridToData(getOriginalCell(edit.location));

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
            const mappedItem = getOriginalCell(item);
            const column = columns[mappedItem[0]];

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
      visibleRows,
      t,
      getOriginalCell,
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
        gridSelection={gridSelection}
        onGridSelectionChange={handleGridSelectionChange}
        readOnly={readOnly}
      />
      {showStats && <MatrixStats stats={selectionStats} />}
    </>
  );
}

export default MatrixGrid;
