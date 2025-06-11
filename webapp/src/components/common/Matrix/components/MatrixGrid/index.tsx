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
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
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
import MatrixStats from "../MatrixStats";

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
  const [gridSelection, setGridSelection] = useState<GridSelection>({
    rows: CompactSelection.empty(),
    columns: CompactSelection.empty(),
  });

  const { gridToData } = useColumnMapping(columns);

  const selectionStats = useSelectionStats({
    data,
    selection: gridSelection,
    gridToData,
  });

  const getCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
    readOnly,
    showPercent,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellEdited = (coordinates: Item, value: EditableGridCell) => {
    if (value.kind !== GridCellKind.Number) {
      // Invalid numeric value
      return;
    }

    const dataCoordinates = gridToData(coordinates);

    if (dataCoordinates && onCellEdit) {
      onCellEdit({ coordinates: dataCoordinates, value });
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit): GridUpdate | null => {
        const dataCoordinates = gridToData(edit.location);

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
            const column = columns[item[0]];

            if (!column.editable || column.type !== GridCellKind.Number) {
              return;
            }

            const coordinates = gridToData(item);

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
              for (let row = 0; row < rows; row++) {
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
    [gridSelection, gridToData, onMultipleCellsEdit, columns, rows, t],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <DataGrid
        key={`matrix-grid-${columns.length}-${data.length}`}
        width={width}
        height={height}
        rows={rows}
        columns={columns}
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
