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

import {
  GridCellKind,
  type EditableGridCell,
  type EditListItem,
  type Item,
} from "@glideapps/glide-data-grid";
import { useGridCellContent } from "../../hooks/useGridCellContent";
import { useMemo } from "react";
import {
  type EnhancedGridColumn,
  type GridUpdate,
  type MatrixAggregates,
} from "../../shared/types";
import { useColumnMapping } from "../../hooks/useColumnMapping";
import { darkTheme, readOnlyDarkTheme } from "../../styles";
import DataGrid from "@/components/common/DataGrid";

export interface MatrixGridProps {
  data: number[][];
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
}: MatrixGridProps) {
  const { gridToData } = useColumnMapping(columns);

  const theme = useMemo(() => {
    if (readOnly) {
      return {
        ...darkTheme,
        ...readOnlyDarkTheme,
      };
    }

    return darkTheme;
  }, [readOnly]);

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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DataGrid
      theme={theme}
      width={width}
      height={height}
      rows={rows}
      columns={columns}
      getCellContent={getCellContent}
      onCellEdited={handleCellEdited}
      onCellsEdited={handleCellsEdited}
      keybindings={{ paste: false, copy: false }}
      getCellsForSelection // TODO handle large copy/paste using this
      fillHandle
      allowedFillDirections="any"
      rowMarkers="both"
      freezeColumns={1} // Make the first column sticky
      cellActivationBehavior="second-click"
    />
  );
}

export default MatrixGrid;
