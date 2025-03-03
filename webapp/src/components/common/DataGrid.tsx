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

import {
  CompactSelection,
  DataEditor,
  GridCellKind,
  type EditListItem,
  type GridSelection,
  type DataEditorProps,
  type GridCell,
} from "@glideapps/glide-data-grid";
import "@glideapps/glide-data-grid/dist/index.css";
import { useCallback, useMemo, useState } from "react";
import { voidFn } from "@/utils/fnUtils";
import { darkTheme, lightTheme, readOnlyDarkTheme, readOnlyLightTheme } from "./Matrix/styles";
import { useUpdateEffect } from "react-use";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

interface StringRowMarkerOptions {
  kind: "string" | "clickable-string";
  getTitle?: (rowIndex: number) => string;
  width?: number;
}

export type RowMarkers =
  | NonNullable<DataEditorProps["rowMarkers"]>
  | StringRowMarkerOptions["kind"]
  | StringRowMarkerOptions;

type RowMarkersOptions = Exclude<RowMarkers, string>;

export interface DataGridProps
  extends Omit<DataEditorProps, "rowMarkers" | "gridSelection" | "theme"> {
  rowMarkers?: RowMarkers;
  enableColumnResize?: boolean;
  readOnly?: boolean;
}

const ROW_HEIGHT = 30;

function isStringRowMarkerOptions(
  rowMarkerOptions: RowMarkersOptions,
): rowMarkerOptions is StringRowMarkerOptions {
  return rowMarkerOptions.kind === "string" || rowMarkerOptions.kind === "clickable-string";
}

function DataGrid({
  rowMarkers = { kind: "none" },
  getCellContent,
  columns: columnsFromProps,
  onCellEdited,
  onCellsEdited,
  onColumnResize,
  onColumnResizeStart,
  onColumnResizeEnd,
  onGridSelectionChange,
  enableColumnResize = true,
  readOnly = false,
  freezeColumns,
  rows,
  ...rest
}: DataGridProps) {
  const rowMarkersOptions: RowMarkersOptions =
    typeof rowMarkers === "string" ? { kind: rowMarkers } : rowMarkers;

  const isStringRowMarkers = isStringRowMarkerOptions(rowMarkersOptions);
  const adjustedFreezeColumns = isStringRowMarkers ? (freezeColumns || 0) + 1 : freezeColumns;

  const [columns, setColumns] = useState(initColumns);
  const [gridSelection, setGridSelection] = useState<GridSelection>({
    rows: CompactSelection.empty(),
    columns: CompactSelection.empty(),
  });

  const { isDarkMode } = useThemeColorScheme();

  const theme = useMemo(() => {
    const baseTheme = isDarkMode ? darkTheme : lightTheme;

    if (readOnly) {
      return {
        ...baseTheme,
        ...(isDarkMode ? readOnlyDarkTheme : readOnlyLightTheme),
      };
    }

    return baseTheme;
  }, [isDarkMode, readOnly]);

  useUpdateEffect(() => {
    setColumns(initColumns());
  }, [columnsFromProps, isStringRowMarkers]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  function initColumns() {
    return isStringRowMarkers
      ? [{ id: "", title: "", width: rowMarkersOptions.width }, ...columnsFromProps]
      : columnsFromProps;
  }

  const ifElseStringRowMarkers = <R1, R2>(
    colIndex: number,
    onTrue: (options: StringRowMarkerOptions) => R1,
    onFalse: (colIndex: number) => R2,
  ) => {
    let adjustedColIndex = colIndex;

    if (isStringRowMarkers) {
      if (colIndex === 0) {
        return onTrue(rowMarkersOptions);
      }

      adjustedColIndex = colIndex - 1;
    }

    return onFalse(adjustedColIndex);
  };

  const ifNotStringRowMarkers = (colIndex: number, fn: (colIndex: number) => void) => {
    return ifElseStringRowMarkers(colIndex, voidFn, fn);
  };

  ////////////////////////////////////////////////////////////////
  // Content
  ////////////////////////////////////////////////////////////////

  const getCellContentWrapper = useCallback<DataEditorProps["getCellContent"]>(
    (cell) => {
      const [colIndex, rowIndex] = cell;

      return ifElseStringRowMarkers(
        colIndex,
        ({ getTitle }) => {
          const title = getTitle ? getTitle(rowIndex) : `Row ${rowIndex + 1}`;

          return {
            kind: GridCellKind.Text,
            data: title,
            displayData: title,
            allowOverlay: false,
            readonly: true,
            themeOverride: {
              bgCell: isDarkMode ? darkTheme.bgHeader : "#efeff1",
            },
          } satisfies GridCell;
        },
        (adjustedColIndex) => {
          return getCellContent([adjustedColIndex, rowIndex]);
        },
      );
    },
    [getCellContent, isStringRowMarkers, isDarkMode],
  );

  ////////////////////////////////////////////////////////////////
  // Edition
  ////////////////////////////////////////////////////////////////

  const handleCellEdited: DataEditorProps["onCellEdited"] = (location, value) => {
    const [colIndex, rowIndex] = location;

    ifNotStringRowMarkers(colIndex, (adjustedColIndex) => {
      onCellEdited?.([adjustedColIndex, rowIndex], value);
    });
  };

  const handleCellsEdited: DataEditorProps["onCellsEdited"] = (items) => {
    if (onCellsEdited) {
      const adjustedItems = items
        .map((item) => {
          const { location } = item;
          const [colIndex, rowIndex] = location;

          return ifElseStringRowMarkers(
            colIndex,
            () => null,
            (adjustedColIndex): EditListItem => {
              return { ...item, location: [adjustedColIndex, rowIndex] };
            },
          );
        })
        .filter(Boolean);

      return onCellsEdited(adjustedItems);
    }
  };

  ////////////////////////////////////////////////////////////////
  // Resize
  ////////////////////////////////////////////////////////////////

  const handleColumnResize: DataEditorProps["onColumnResize"] =
    onColumnResize || enableColumnResize
      ? (column, newSize, colIndex, newSizeWithGrow) => {
          if (enableColumnResize) {
            setColumns(
              columns.map((col, index) => (index === colIndex ? { ...col, width: newSize } : col)),
            );
          }

          if (onColumnResize) {
            ifNotStringRowMarkers(colIndex, (adjustedColIndex) => {
              onColumnResize(column, newSize, adjustedColIndex, newSizeWithGrow);
            });
          }
        }
      : undefined;

  const handleColumnResizeStart: DataEditorProps["onColumnResizeStart"] = onColumnResizeStart
    ? (column, newSize, colIndex, newSizeWithGrow) => {
        ifNotStringRowMarkers(colIndex, (adjustedColIndex) => {
          onColumnResizeStart(column, newSize, adjustedColIndex, newSizeWithGrow);
        });
      }
    : undefined;

  const handleColumnResizeEnd: DataEditorProps["onColumnResizeEnd"] = onColumnResizeEnd
    ? (column, newSize, colIndex, newSizeWithGrow) => {
        ifNotStringRowMarkers(colIndex, (adjustedColIndex) => {
          onColumnResizeEnd(column, newSize, adjustedColIndex, newSizeWithGrow);
        });
      }
    : undefined;

  ////////////////////////////////////////////////////////////////
  // Selection
  ////////////////////////////////////////////////////////////////

  const handleGridSelectionChange = (newSelection: GridSelection) => {
    {
      if (isStringRowMarkers) {
        if (newSelection.current) {
          // Select the whole row when clicking on a row marker cell
          if (rowMarkersOptions.kind === "clickable-string" && newSelection.current.cell[0] === 0) {
            setGridSelection({
              ...newSelection,
              current: undefined,
              rows: CompactSelection.fromSingleSelection(newSelection.current.cell[1]),
            });

            return;
          }

          // Prevent selecting a row marker cell
          if (newSelection.current.range.x === 0) {
            return;
          }
        }

        // Select/Deselect all the rows like others row markers when selecting the column
        if (newSelection.columns.hasIndex(0)) {
          const isSelectedAll = gridSelection.rows.length === rows;

          setGridSelection({
            ...newSelection,
            columns: CompactSelection.empty(),
            rows: isSelectedAll
              ? CompactSelection.empty()
              : CompactSelection.fromSingleSelection([0, rows]),
          });

          return;
        }
      }

      setGridSelection(newSelection);
      onGridSelectionChange?.(newSelection);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DataEditor
      groupHeaderHeight={ROW_HEIGHT}
      headerHeight={ROW_HEIGHT}
      rowHeight={ROW_HEIGHT}
      smoothScrollX
      smoothScrollY
      width="100%"
      theme={theme}
      rows={rows}
      columns={columns}
      rowMarkers={isStringRowMarkers ? "none" : rowMarkersOptions}
      getCellContent={getCellContentWrapper}
      onCellEdited={handleCellEdited}
      onCellsEdited={handleCellsEdited}
      onColumnResize={handleColumnResize}
      onColumnResizeStart={handleColumnResizeStart}
      onColumnResizeEnd={handleColumnResizeEnd}
      gridSelection={gridSelection}
      onGridSelectionChange={handleGridSelectionChange}
      freezeColumns={adjustedFreezeColumns}
      {...rest}
    />
  );
}

export default DataGrid;
