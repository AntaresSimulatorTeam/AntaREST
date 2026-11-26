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

import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import { voidFn } from "@/utils/fnUtils";
import {
  CompactSelection,
  DataEditor,
  GridCellKind,
  isEditableGridCell,
  type CellClickedEventArgs,
  type DataEditorProps,
  type EditListItem,
  type GridColumn,
  type GridSelection,
  type Item,
  type LoadingCell,
  type Slice,
  type TextCell,
  type ValidatedGridCell,
} from "@glideapps/glide-data-grid";
import "@glideapps/glide-data-grid/dist/index.css";
import { produce } from "immer";
import * as R from "ramda";
import { useCallback, useImperativeHandle, useMemo, useRef, useState } from "react";
import { usePrevious, useUpdateEffect } from "react-use";
import DataGridSkeleton from "../DataGridSkeleton";
import { darkTheme, lightTheme, readOnlyDarkTheme, readOnlyLightTheme } from "../Matrix/styles";

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

export interface DataGridHandle {
  /**
   * Grows the given columns to the new widths (never shrinks them).
   *
   * Lets callers (e.g. a paste handler) grow columns without resetting `columns`
   * from props, which would discard the user's manual resizes.
   *
   * @param updates - New widths, keyed by column id.
   */
  resizeColumns: (updates: Map<string, number>) => void;
}

export interface DataGridProps extends Omit<DataEditorProps, "rowMarkers" | "theme"> {
  ref?: React.Ref<DataGridHandle>;
  /** Omit or pass undefined for internal selection state; keep the control mode stable while mounted. */
  gridSelection?: GridSelection;
  /**
   * Emitted whenever the grid selection changes.
   *
   * Unlike Glide's `DataEditor`, specifying this function does NOT make the selection
   * controlled: the selection is controlled only if `gridSelection` is provided.
   * Without it, the selection is managed internally and this callback only notifies changes.
   *
   * @param newSelection - The new selection.
   */
  onGridSelectionChange?: DataEditorProps["onGridSelectionChange"];
  rowMarkers?: RowMarkers;
  enableColumnResize?: boolean;
  readOnly?: boolean;
  isLoading?: boolean;
}

function isStringRowMarkerOptions(
  rowMarkerOptions: RowMarkersOptions,
): rowMarkerOptions is StringRowMarkerOptions {
  return rowMarkerOptions.kind === "string" || rowMarkerOptions.kind === "clickable-string";
}

function buildStringRowMarkerColumn(width?: number): GridColumn {
  return { id: "", title: "", width };
}

function DataGrid({
  rowMarkers = { kind: "none" },
  getCellContent,
  columns: columnsFromProps,
  onCellEdited,
  onCellsEdited,
  onCellClicked,
  onColumnResize,
  onColumnResizeStart,
  onColumnResizeEnd,
  onGridSelectionChange,
  onRowAppended,
  onDelete,
  onPaste,
  gridSelection: controlledSelection,
  fillHandle,
  enableColumnResize = true,
  readOnly = false,
  isLoading = false,
  freezeColumns,
  rows,
  ref,
  rowSelect = "multi",
  rowSelectionMode,
  ...rest
}: DataGridProps) {
  const rowMarkersOptions: RowMarkersOptions =
    typeof rowMarkers === "string" ? { kind: rowMarkers } : rowMarkers;
  const isStringRowMarkers = isStringRowMarkerOptions(rowMarkersOptions);
  const adjustedFreezeColumns = isStringRowMarkers ? (freezeColumns || 0) + 1 : freezeColumns;
  const [columns, setColumns] = useState(initColumns);
  const [internalSelection, setInternalSelection] = useState<GridSelection>({
    rows: CompactSelection.empty(),
    columns: CompactSelection.empty(),
  });
  const prevRows = usePrevious(rows);
  const gridSelection = controlledSelection ?? internalSelection;
  // Last row clicked without Shift: starting point of Shift+click range selections
  const rowSelectionAnchorRef = useRef<number | null>(null);
  const canEdit = !readOnly && !isLoading;

  useImperativeHandle(ref, () => ({
    resizeColumns(updates: Map<string, number>) {
      setColumns((prev) =>
        prev.map((col) => {
          const colId = col.id;
          if (!colId) {
            return col;
          }

          const newWidth = updates.get(colId);

          if (newWidth === undefined) {
            return col;
          }

          const currentWidth = "width" in col ? (col.width ?? 0) : 0;

          if (newWidth <= currentWidth) {
            return col;
          }

          return { ...col, width: newWidth };
        }),
      );
    },
  }));

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
    // `rowMarkersOptions.width` omitted: a width change only updates the marker column
    // (effect below), to keep the user's manual resizes of the data columns.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columnsFromProps, isStringRowMarkers]);

  // Only update the string row marker column when its width changes,
  // to keep the user's manual resizes of the data columns
  useUpdateEffect(() => {
    if (isStringRowMarkers) {
      setColumns(
        produce((draft) => {
          draft[0] = buildStringRowMarkerColumn(rowMarkersOptions.width);
        }),
      );
    }
  }, [isStringRowMarkers, rowMarkersOptions.width]);

  // Row indexes are no longer valid when rows are removed: clear the row selection
  // and the range anchor. Appending rows keeps existing indexes valid, so the selection
  // is kept (e.g. a controlled parent selecting the newly appended row).
  useUpdateEffect(() => {
    if (prevRows === undefined || rows >= prevRows) {
      return;
    }

    rowSelectionAnchorRef.current = null;

    if (gridSelection.rows.length > 0) {
      updateGridSelection({
        ...gridSelection,
        current: undefined,
        rows: CompactSelection.empty(),
      });
    }
  }, [rows]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  function initColumns() {
    return isStringRowMarkers
      ? [buildStringRowMarkerColumn(rowMarkersOptions.width), ...columnsFromProps]
      : columnsFromProps;
  }

  function updateGridSelection(selection: GridSelection) {
    if (controlledSelection === undefined) {
      setInternalSelection(selection);
    }

    onGridSelectionChange?.(selection);
  }

  const ifElseStringMarkerColumn = <R1, R2>(
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

  const ifNotStringMarkerColumn = (colIndex: number, fn: (colIndex: number) => void) => {
    return ifElseStringMarkerColumn(colIndex, voidFn, fn);
  };

  ////////////////////////////////////////////////////////////////
  // Content
  ////////////////////////////////////////////////////////////////

  const getCellContentWrapper = useCallback<DataEditorProps["getCellContent"]>(
    (cell) => {
      const [colIndex, rowIndex] = cell;

      return ifElseStringMarkerColumn(
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
          } satisfies TextCell;
        },
        (adjustedColIndex) => {
          if (isLoading) {
            return {
              kind: GridCellKind.Loading,
              skeletonWidth: 40,
              skeletonWidthVariability: 10,
              allowOverlay: false,
            } satisfies LoadingCell;
          }

          const gridCell = getCellContent([adjustedColIndex, rowIndex]);

          if (readOnly && isEditableGridCell(gridCell)) {
            return {
              ...gridCell,
              readonly: true,
              allowOverlay: false,
            } satisfies ValidatedGridCell;
          }

          return gridCell;
        },
      );
    },
    // TODO: add `rowMarkersOptions` (used in `ifElseStringRowMarkers`) once it's memoized
    [getCellContent, isStringRowMarkers, isDarkMode, isLoading, readOnly],
  );

  ////////////////////////////////////////////////////////////////
  // Edition
  ////////////////////////////////////////////////////////////////

  const handleCellEdited: DataEditorProps["onCellEdited"] = (location, value) => {
    const [colIndex, rowIndex] = location;

    if (onCellEdited) {
      ifNotStringMarkerColumn(colIndex, (adjustedColIndex) => {
        onCellEdited([adjustedColIndex, rowIndex], value);
      });
    }
  };

  const handleCellsEdited: DataEditorProps["onCellsEdited"] = (items) => {
    if (onCellsEdited) {
      const adjustedItems = items
        .map((item) => {
          const { location } = item;
          const [colIndex, rowIndex] = location;

          return ifElseStringMarkerColumn(
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

  // Glide only shows the trailing row when `onRowAppended` is set, and some callers use it
  // to display content (e.g. totals): keep it visible but inert when editing is disabled
  const handleRowAppended: DataEditorProps["onRowAppended"] =
    onRowAppended && (canEdit ? onRowAppended : voidFn);

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
            ifNotStringMarkerColumn(colIndex, (adjustedColIndex) => {
              onColumnResize(column, newSize, adjustedColIndex, newSizeWithGrow);
            });
          }
        }
      : undefined;

  const handleColumnResizeStart: DataEditorProps["onColumnResizeStart"] = onColumnResizeStart
    ? (column, newSize, colIndex, newSizeWithGrow) => {
        ifNotStringMarkerColumn(colIndex, (adjustedColIndex) => {
          onColumnResizeStart(column, newSize, adjustedColIndex, newSizeWithGrow);
        });
      }
    : undefined;

  const handleColumnResizeEnd: DataEditorProps["onColumnResizeEnd"] = onColumnResizeEnd
    ? (column, newSize, colIndex, newSizeWithGrow) => {
        ifNotStringMarkerColumn(colIndex, (adjustedColIndex) => {
          onColumnResizeEnd(column, newSize, adjustedColIndex, newSizeWithGrow);
        });
      }
    : undefined;

  ////////////////////////////////////////////////////////////////
  // Selection
  ////////////////////////////////////////////////////////////////

  /**
   * Handles every selection change coming from Glide (cell click, drag, keyboard, header click…).
   *
   * With string row markers (column 0), two cases are intercepted:
   * - Cells of the marker column must never be selected as cells: row selection
   *   on marker click is handled by `handleCellClicked`, which has access to modifier keys.
   * - Clicking the marker column header selects/deselects all rows when `rowSelect` is "multi",
   *   like Glide's native row markers.
   *
   * Any other change is forwarded as is.
   *
   * @param newSelection - The new selection state coming from the grid.
   */
  const handleGridSelectionChange = (newSelection: GridSelection) => {
    if (isStringRowMarkers) {
      // Ignore any cell selection touching the marker column (click, drag, Shift+click or Shift+arrow into it)
      if (newSelection.current?.range.x === 0) {
        return;
      }

      // Marker column header clicked
      if (newSelection.columns.hasIndex(0)) {
        // Selecting all rows is only allowed in multi row selection
        if (rowSelect !== "multi") {
          return;
        }

        // Toggle between all rows selected and none
        const isSelectedAll = gridSelection.rows.length === rows;

        updateGridSelection({
          ...newSelection,
          columns: CompactSelection.empty(),
          rows: isSelectedAll
            ? CompactSelection.empty()
            : CompactSelection.fromSingleSelection([0, rows]),
        });

        return;
      }
    }

    updateGridSelection(newSelection);
  };

  /**
   * Handles row selection when a "clickable-string" row marker is clicked,
   * mirroring Glide's native row markers behavior (e.g. `checkbox`) and its
   * `rowSelect` and `rowSelectionMode` props:
   * - `rowSelect` "none": rows can't be selected
   * - `rowSelect` "single": click selects only this row, or deselects it if already selected
   * - `rowSelect` "multi", in addition:
   *   - Ctrl/Cmd + click (or tap on touch devices): add/remove this row to/from the selection.
   *     With `rowSelectionMode` "multi", a plain click behaves the same way.
   *   - Shift + click (or long touch): select the range from the anchor row to this row,
   *     added to the selection when combined with Ctrl/Cmd or with `rowSelectionMode` "multi"
   *
   * Done here rather than in `handleGridSelectionChange` because Glide's `onGridSelectionChange`
   * doesn't provide the mouse event, so modifier keys can't be read there.
   *
   * @param cell - The clicked cell, as `[col, row]`.
   * @param event - The click event, used to read the modifier keys.
   */
  const handleCellClicked = (cell: Item, event: CellClickedEventArgs) => {
    const [col, row] = cell;

    if (onCellClicked) {
      // Same indexes as Glide's native row markers: -1 for the marker column
      ifElseStringMarkerColumn(
        col,
        () => onCellClicked([-1, row], event),
        (adjustedColIndex) => onCellClicked([adjustedColIndex, row], event),
      );
    }

    // Only handle clicks on a "clickable-string" row marker of a data row, when row selection is enabled
    // (`row === rows` is the trailing row used to append rows, handled by Glide)
    if (
      rowMarkersOptions.kind !== "clickable-string" ||
      col !== 0 ||
      row >= rows ||
      rowSelect === "none"
    ) {
      return;
    }

    const selectedRows = gridSelection.rows;
    const isMultiRowSelect = rowSelect === "multi";
    const isMultiKey = event.ctrlKey || event.metaKey; // Ctrl on Windows/Linux, Cmd on macOS
    const isMultiSelect =
      isMultiRowSelect && (isMultiKey || event.isTouch || rowSelectionMode === "multi");
    const isRangeSelect = isMultiRowSelect && (event.shiftKey || event.isLongTouch === true);
    const anchor = rowSelectionAnchorRef.current;

    let nextRows: CompactSelection;

    // Range selection (Shift + click or long touch), only if the anchor row is still selected.
    // Otherwise, falls back to the cases below like Glide does.
    if (isRangeSelect && anchor !== null && selectedRows.hasIndex(anchor)) {
      // The anchor is kept, so successive Shift+clicks resize the range from it.
      // Slice end is exclusive, hence the +1.
      const range: Slice = [Math.min(anchor, row), Math.max(anchor, row) + 1];

      nextRows = isMultiSelect
        ? selectedRows.add(range) // Extend the current selection with the range
        : CompactSelection.fromSingleSelection(range); // Replace the selection with the range
    }
    // Toggle selection (Ctrl/Cmd + click, tap on touch devices, or `rowSelectionMode` "multi")
    else if (isMultiSelect) {
      // Already selected: deselect it (anchor unchanged)
      if (selectedRows.hasIndex(row)) {
        nextRows = selectedRows.remove(row);
      }
      // Not selected: add it and make it the new anchor
      else {
        nextRows = selectedRows.add(row);
        rowSelectionAnchorRef.current = row;
      }
    }
    // Plain click on the only selected row: deselect it
    else if (selectedRows.hasIndex(row) && selectedRows.length === 1) {
      nextRows = CompactSelection.empty();
    }
    // Plain click: select only this row and make it the new anchor
    else {
      nextRows = CompactSelection.fromSingleSelection(row);
      rowSelectionAnchorRef.current = row;
    }

    // Row selection only: clear any cell or column selection
    updateGridSelection({
      current: undefined,
      columns: CompactSelection.empty(),
      rows: nextRows,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // `isLoading` displays loading cells, but with no rows there are no cells
  // to display it: render a skeleton grid instead
  if (isLoading && rows === 0) {
    return <DataGridSkeleton readOnly={readOnly} />;
  }

  return (
    <DataEditor
      groupHeaderHeight={35}
      headerHeight={25}
      rowHeight={30}
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
      onCellClicked={handleCellClicked}
      onColumnResize={handleColumnResize}
      onColumnResizeStart={handleColumnResizeStart}
      onColumnResizeEnd={handleColumnResizeEnd}
      onRowAppended={handleRowAppended}
      onDelete={canEdit ? onDelete : R.F}
      onPaste={canEdit ? onPaste : false}
      gridSelection={gridSelection}
      onGridSelectionChange={handleGridSelectionChange}
      freezeColumns={adjustedFreezeColumns}
      rowSelect={rowSelect}
      rowSelectionMode={rowSelectionMode}
      fillHandle={canEdit ? fillHandle : false}
      {...rest}
    />
  );
}

export default DataGrid;
