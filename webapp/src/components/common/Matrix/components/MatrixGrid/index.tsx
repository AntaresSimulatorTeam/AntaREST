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

import DataGrid from "@/components/common/DataGrid";
import {
  CompactSelection,
  GridCellKind,
  type EditableGridCell,
  type EditListItem,
  type GridKeyEventArgs,
  type GridSelection,
  type Item,
} from "@glideapps/glide-data-grid";
import { useGridCellContent } from "../../hooks/useGridCellContent";
import { useCallback, useMemo, useState } from "react";
import DataGrid from "@/components/common/DataGrid";
import { useColumnMapping } from "../../hooks/useColumnMapping";
import { useGridCellContent } from "../../hooks/useGridCellContent";
import { useSelectionStats } from "../../hooks/useSelectionStats";
import type {
  EnhancedGridColumn,
  GridUpdate,
  MatrixAggregates,
  NonEmptyMatrix,
} from "../../shared/types";
import { formatGridNumber } from "../../shared/utils";
import { useTranslation } from "react-i18next";
import { useMatrixContext } from "../../context/MatrixContext";
import { Column } from "../../shared/constants";

export interface MatrixGridProps {
  data: NonEmptyMatrix;
  rows: number;
  columns: readonly EnhancedGridColumn[];
  dateTime?: string[];
  aggregates?: Partial<MatrixAggregates>;
  rowHeaders?: string[];
  width?: string;
  height?: string;
  onCellEdit?: (update: GridUpdate) => void;
  onMultipleCellsEdit?: (updates: GridUpdate[]) => void;
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
  readOnly,
  showPercent,
  showStats = true,
}: MatrixGridProps) {
  const { t } = useTranslation();
  const { filterPreview } = useMatrixContext();
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
      const [col, visibleRow] = cell;
      const dataRow = getDataRowIndex(visibleRow);

      const mappedCell: Item = [col, dataRow];

      return originalGetCellContent(mappedCell);
    },
    [getDataRowIndex, originalGetCellContent],
  );

  const selectionStats = useSelectionStats({
    data,
    selection: gridSelection,
    gridToData,
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
            const originalCol = filterPreview.active
              ? columns.findIndex((col) => col.id === visibleColumns[visibleCol].id)
              : visibleCol;

            const mappedItem: Item = [originalCol, dataRow];

            const column = filterPreview.active ? visibleColumns[visibleCol] : columns[originalCol];

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
              for (let col = 0; col < columns.length; col++) {
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
        key={`matrix-grid-${visibleColumns.length}-${data.length}`}
        width={width}
        height={height}
        rows={visibleRows}
        columns={visibleColumns}
        getCellContent={getCellContent}
        onCellEdited={handleCellEdited}
        onCellsEdited={handleCellsEdited}
        getCellsForSelection
        onPaste={!readOnly}
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
