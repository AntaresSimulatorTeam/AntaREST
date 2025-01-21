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
  CompactSelection,
  DataEditor,
  GridCellKind,
  type EditListItem,
  type GridSelection,
  type DataEditorProps,
} from "@glideapps/glide-data-grid";
import "@glideapps/glide-data-grid/dist/index.css";
import { useCallback, useEffect, useState } from "react";
import { voidFn } from "@/utils/fnUtils";
import { darkTheme } from "./Matrix/styles";

interface StringRowMarkerOptions {
  kind: "string" | "clickable-string";
  getTitle?: (rowIndex: number) => string;
}

type RowMarkers =
  | NonNullable<DataEditorProps["rowMarkers"]>
  | StringRowMarkerOptions["kind"]
  | StringRowMarkerOptions;

type RowMarkersOptions = Exclude<RowMarkers, string>;

export interface DataGridProps
  extends Omit<DataEditorProps, "rowMarkers" | "onGridSelectionChange" | "gridSelection"> {
  rowMarkers?: RowMarkers;
  enableColumnResize?: boolean;
}

function isStringRowMarkerOptions(
  rowMarkerOptions: RowMarkersOptions,
): rowMarkerOptions is StringRowMarkerOptions {
  return rowMarkerOptions.kind === "string" || rowMarkerOptions.kind === "clickable-string";
}

function DataGrid(props: DataGridProps) {
  const {
    rowMarkers = { kind: "none" },
    getCellContent,
    columns: columnsFromProps,
    onCellEdited,
    onCellsEdited,
    onColumnResize,
    onColumnResizeStart,
    onColumnResizeEnd,
    enableColumnResize = true,
    freezeColumns,
    ...rest
  } = props;

  const rowMarkersOptions: RowMarkersOptions =
    typeof rowMarkers === "string" ? { kind: rowMarkers } : rowMarkers;
  const isStringRowMarkers = isStringRowMarkerOptions(rowMarkersOptions);
  const adjustedFreezeColumns = isStringRowMarkers ? (freezeColumns || 0) + 1 : freezeColumns;

  const [columns, setColumns] = useState(columnsFromProps);
  const [selection, setSelection] = useState<GridSelection>({
    columns: CompactSelection.empty(),
    rows: CompactSelection.empty(),
  });

  // Add a column for the "string" row markers if needed
  useEffect(() => {
    setColumns(
      isStringRowMarkers ? [{ id: "", title: "" }, ...columnsFromProps] : columnsFromProps,
    );
  }, [columnsFromProps, isStringRowMarkers]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const ifElseStringRowMarkers = <R1, R2>(
    colIndex: number,
    onTrue: () => R1,
    onFalse: (colIndex: number) => R2,
  ) => {
    let adjustedColIndex = colIndex;

    if (isStringRowMarkers) {
      if (colIndex === 0) {
        return onTrue();
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
        () => {
          const title =
            isStringRowMarkers && rowMarkersOptions.getTitle
              ? rowMarkersOptions.getTitle(rowIndex)
              : `Row ${rowIndex + 1}`;

          return {
            kind: GridCellKind.Text,
            data: title,
            displayData: title,
            allowOverlay: false,
            readonly: true,
            themeOverride: {
              bgCell: darkTheme.bgHeader,
            },
          };
        },
        (adjustedColIndex) => {
          return getCellContent([adjustedColIndex, rowIndex]);
        },
      );
    },
    [getCellContent, isStringRowMarkers],
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
            setSelection({
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

        // Prevent selecting the row marker column
        if (newSelection.columns.hasIndex(0)) {
          // TODO find a way to have the rows length to select all the rows like other row markers
          // setSelection({
          //   ...newSelection,
          //   columns: CompactSelection.empty(),
          //   rows: CompactSelection.fromSingleSelection([
          //     0,
          //     // rowsLength
          //   ]),
          // });

          setSelection({
            ...newSelection,
            columns: newSelection.columns.remove(0),
          });

          return;
        }
      }

      setSelection(newSelection);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DataEditor
      groupHeaderHeight={30}
      headerHeight={30}
      rowHeight={30}
      smoothScrollX
      smoothScrollY
      overscrollX={2}
      overscrollY={2}
      width="100%"
      theme={darkTheme}
      {...rest}
      columns={columns}
      rowMarkers={isStringRowMarkers ? "none" : rowMarkersOptions}
      getCellContent={getCellContentWrapper}
      onCellEdited={handleCellEdited}
      onCellsEdited={handleCellsEdited}
      onColumnResize={handleColumnResize}
      onColumnResizeStart={handleColumnResizeStart}
      onColumnResizeEnd={handleColumnResizeEnd}
      gridSelection={selection}
      onGridSelectionChange={handleGridSelectionChange}
      freezeColumns={adjustedFreezeColumns}
    />
  );
}

export default DataGrid;
