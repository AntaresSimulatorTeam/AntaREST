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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormBlocker from "@/hooks/useFormBlocker";
import { getColumnWidth } from "@/utils/dataGridUtils";
import { toError } from "@/utils/fnUtils";
import { mergeSxProp } from "@/utils/muiUtils";
import {
  CompactSelection,
  GridCellKind,
  type DataEditorProps,
  type GridColumn,
  type GridSelection,
  type Item,
} from "@glideapps/glide-data-grid";
import DeleteIcon from "@mui/icons-material/Delete";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import UndoIcon from "@mui/icons-material/Undo";
import {
  Box,
  Button,
  Divider,
  IconButton,
  setRef,
  Stack,
  Tooltip,
  type ButtonProps,
  type SxProps,
  type Theme,
} from "@mui/material";
import { produce } from "immer";
import * as R from "ramda";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useUndo, { type Actions } from "use-undo";
import DataGrid, { type DataGridProps, type RowMarkers } from "./DataGrid";
import type { SubmitHandlerPlus } from "./Form/types";

type Data = Record<string, Record<string, string | boolean | number>>;

export interface DataGridFormState {
  isDirty: boolean;
  isSubmitting: boolean;
}

export interface DataGridFormApi<TData extends Data> {
  data: TData;
  setData: Actions<TData>["set"];
  formState: DataGridFormState;
}

interface Changes<TData extends Data> {
  /** Rows present in the current data but not in the saved data, keyed by row ID. */
  added: Partial<TData>;
  /** Rows present in both, containing only the values that differ from the saved data, keyed by row ID. */
  updated: Partial<TData>;
  /** IDs of rows present in the saved data but no longer in the current data. */
  // Typed as `string` rather than `keyof TData`, which can include numbers,
  // because object keys are always strings at runtime.
  deleted: string[];
}

export interface DataGridFormSubmitData<TData extends Data = Data>
  extends SubmitHandlerPlus<TData> {
  /** Row-level changes: added, updated and deleted rows */
  changes: Changes<TData>;
  /**
   * Marks a row as saved as soon as its request succeeds.
   * Useful when `onSubmit` sends several requests: if one fails, the rows
   * already saved won't be included again in the next submit's changes.
   */
  markAsSaved: (rowName: string) => void;
}

export interface DataGridFormProps<TData extends Data = Data, SubmitReturnValue = unknown> {
  defaultData: TData;
  columns: ReadonlyArray<GridColumn & { id: keyof TData[string] }>;
  rowMarkers?: DataGridProps["rowMarkers"];
  allowedFillDirections?: DataGridProps["allowedFillDirections"];
  onRowAppended?: DataGridProps["onRowAppended"];
  trailingRowOptions?: DataGridProps["trailingRowOptions"];
  enableColumnResize?: boolean;
  getCellContent?: (
    location: Item,
    data: TData[string][keyof TData[string]],
  ) => ReturnType<DataEditorProps["getCellContent"]>;
  /**
   * Transforms an edited value before it's stored.
   *
   * Called for each edited cell (typing, paste, fill or delete).
   *
   * @param location - The edited cell, as `[col, row]`.
   * @param newValue - The value entered in the cell.
   * @param data - The data before the edit. When several cells are edited at once
   * (paste or fill), it doesn't include the new values of the other edited cells.
   * @returns The value to store instead, or `undefined` to store the entered value as is.
   */
  transformCellValue?: (
    location: Item,
    newValue: unknown,
    data: TData,
  ) => TData[string][keyof TData[string]] | undefined;
  onSubmit: (
    data: DataGridFormSubmitData<TData>,
    event: React.SubmitEvent<HTMLFormElement>,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: DataGridFormSubmitData<TData>,
    submitResult: SubmitReturnValue,
  ) => void;
  onDataChange?: (data: TData) => void;
  onStateChange?: (state: DataGridFormState) => void;
  id?: string;
  sx?: SxProps<Theme>;
  extraActions?: React.ReactNode | ((state: { canSubmit: boolean }) => React.ReactNode);
  apiRef?: React.Ref<DataGridFormApi<TData>>;
  submitButtonText?: string;
  submitButtonIcon?: ButtonProps["startIcon"];
  hideSubmitButton?: boolean;
  disableErrorSnackbar?: boolean;
  isLoading?: boolean;
  readOnly?: boolean;
  allowRowDeletion?: boolean;
}

function isValidCellValue<TData extends Data>(
  value: unknown,
): value is TData[string][keyof TData[string]] {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean";
}

function DataGridForm<TData extends Data>({
  defaultData,
  columns,
  allowedFillDirections = "vertical",
  rowMarkers: rowMarkersFromProps,
  getCellContent: getCellContentFromProps,
  transformCellValue,
  onSubmit,
  onSubmitSuccessful,
  onDataChange,
  onStateChange,
  sx,
  id,
  extraActions,
  apiRef,
  submitButtonText,
  submitButtonIcon = <SaveIcon />,
  hideSubmitButton = false,
  disableErrorSnackbar = false,
  isLoading = false,
  readOnly = false,
  allowRowDeletion = false,
  ...dataGridProps
}: DataGridFormProps<TData>) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedData, setSavedData] = useState(defaultData);
  const [error, setError] = useState<string | null>(null);
  const [selectedRows, setSelectedRows] = useState(CompactSelection.empty());

  const [{ present: data }, { set: setData, undo, redo, canUndo: hasUndo, canRedo: hasRedo }] =
    useUndo(defaultData);
  const rowNames = useMemo(() => Object.keys(data), [data]);

  // Compare contents rather than references (`savedData !== data`) or `getChanges()`:
  // - `markAsSaved` creates a new `savedData` object for each saved row. After a partially
  //   failed submit, `savedData` is therefore never the same object as `data`, even if the user
  //   then reverts the unsaved changes, so a reference comparison would keep the form dirty.
  // - `getChanges()` doesn't report removed column keys, so it would consider the form clean.
  // `R.equals` stays cheap: it compares references first at each level, so it returns
  // immediately when `data` is `savedData` and skips unedited rows.
  const isDirty = useMemo(() => !R.equals(savedData, data), [savedData, data]);

  const canEdit = !isSubmitting && !isLoading && !readOnly;
  const canSubmit = isDirty && canEdit;
  const canUndo = hasUndo && canEdit;
  const canRedo = hasRedo && canEdit;
  const canDelete = allowRowDeletion && canEdit;
  const hasSelectedRows = selectedRows.length > 0;

  const formState = useMemo<DataGridFormState>(
    () => ({
      isDirty,
      isSubmitting,
    }),
    [isDirty, isSubmitting],
  );

  useFormBlocker({ isSubmitting, isDirty });

  useUpdateEffect(() => onDataChange?.(data), [data]);

  useUpdateEffect(() => onStateChange?.(formState), [formState]);

  useEffect(() => setRef(apiRef, { data, setData, formState }), [apiRef, data, setData, formState]);

  const columnsWithAdjustedSize = useMemo(
    () =>
      columns.map((column) => ({
        ...column,
        width: getColumnWidth(column, () =>
          rowNames.map((rowName) => data[rowName][column.id]?.toString()),
        ),
      })),
    [columns, data, rowNames],
  );

  const columnIds = useMemo(() => columns.map((column) => column.id), [columns]);

  const rowMarkers = useMemo<RowMarkers>(
    () =>
      rowMarkersFromProps || {
        kind: "clickable-string",
        getTitle: (index) => rowNames[index],
        width: getColumnWidth({ title: "", id: "" }, () => rowNames),
      },
    [rowMarkersFromProps, rowNames],
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getRowAndColumnNames = useCallback(
    (location: Item) => {
      const [colIndex, rowIndex] = location;
      return [rowNames[rowIndex], columnIds[colIndex]];
    },
    [rowNames, columnIds],
  );

  /**
   * Computes the modified columns of the existing rows (rows present in both
   * the saved data and the current data).
   *
   * Added and deleted rows are ignored: they are handled in `getChanges`.
   *
   * @returns An object containing, for each modified row, only its modified columns.
   */
  const getDirtyValues = () => {
    // Plain loops with a mutable accumulator: a `reduce` spreading the accumulator
    // would copy it for each row, which gets very slow with many dirty rows
    const dirtyValues: Changes<TData>["updated"] = {};

    for (const rowName of rowNames) {
      const rowData = data[rowName];
      const savedRowData = savedData[rowName];

      // Same reference: the row hasn't been edited (edits always create a new row object)
      if (rowData === savedRowData) {
        continue;
      }

      // Added or deleted row: not an update, handled in `getChanges`.
      // `Object.hasOwn` rather than a truthiness check: for a row missing from the object,
      // `savedData[rowName]` can return an inherited property (e.g. "constructor").
      if (!Object.hasOwn(data, rowName) || !Object.hasOwn(savedData, rowName)) {
        continue;
      }

      let dirtyColumns: Partial<TData[string]> | undefined;

      // `Object.assign` because TypeScript rejects direct writes to generic `TData` keys

      for (const columnName in rowData) {
        if (!Object.hasOwn(rowData, columnName)) {
          continue;
        }

        if (rowData[columnName] !== savedRowData[columnName]) {
          dirtyColumns ??= {};
          Object.assign(dirtyColumns, { [columnName]: rowData[columnName] });
        }
      }

      if (dirtyColumns) {
        Object.assign(dirtyValues, { [rowName]: dirtyColumns });
      }
    }

    return dirtyValues;
  };

  /**
   * Computes the row-level changes between the saved data and the current data.
   *
   * @returns An object containing:
   * - `added`: rows that are not in the saved data, with all their values
   * - `updated`: existing rows, with only their modified columns (same as `getDirtyValues`)
   * - `deleted`: names of the rows that are no longer in the current data
   */
  const getChanges = (): Changes<TData> => {
    const added: Partial<TData> = {};
    const deleted: string[] = [];

    // Row not in saved data → added
    for (const rowName in data) {
      if (!Object.hasOwn(savedData, rowName)) {
        added[rowName] = data[rowName];
      }
    }

    // Row in saved data but no longer in current data → deleted
    for (const rowName in savedData) {
      if (!Object.hasOwn(data, rowName)) {
        deleted.push(rowName);
      }
    }

    return {
      added,
      updated: getDirtyValues(),
      deleted,
    };
  };

  /**
   * Marks a row as saved by syncing it in `savedData` with its submitted value.
   *
   * Passed to `onSubmit` for submits that send several requests: if one fails,
   * the rows already saved won't be included again in the next submit's changes.
   *
   * @param rowName - Name of the row whose request succeeded (added, updated or deleted).
   */
  const markAsSaved = (rowName: string) => {
    // Functional update so successive calls don't overwrite each other.
    // `produce` returns `prev` when nothing changes.
    setSavedData((prev) =>
      produce(prev, (draft) => {
        if (Object.hasOwn(data, rowName)) {
          // Added or updated row.
          // `Object.assign` because TypeScript rejects direct writes to generic `TData` keys.
          Object.assign(draft, { [rowName]: data[rowName] });
        } else if (Object.hasOwn(draft, rowName)) {
          // Deleted row.
          // The own-property check matters: Immer detects keys through the
          // prototype chain (`in`), so deleting a missing inherited key such as
          // "toString" would still produce a new object.
          delete draft[rowName];
        }
      }),
    );
  };

  /**
   * Deletes the given rows.
   *
   * @param rowIndexes - Indexes of the rows to delete.
   */
  const deleteRows = (rowIndexes: number[]) => {
    setData(
      produce(data, (draft) => {
        for (const rowIndex of rowIndexes) {
          const rowName = rowNames[rowIndex];

          if (rowName !== undefined && Object.hasOwn(draft, rowName)) {
            delete draft[rowName];
          }
        }
      }),
    );
  };

  ////////////////////////////////////////////////////////////////
  // Content
  ////////////////////////////////////////////////////////////////

  const getCellContent = useCallback<DataEditorProps["getCellContent"]>(
    (location) => {
      const [rowName, columnName] = getRowAndColumnNames(location);
      const dataRow = data[rowName];
      const cellData = dataRow[columnName];

      // Use custom getCellContent if provided
      if (getCellContentFromProps) {
        return getCellContentFromProps(location, cellData as TData[string][keyof TData[string]]);
      }

      if (typeof cellData === "string") {
        return {
          kind: GridCellKind.Text,
          data: cellData,
          displayData: cellData,
          allowOverlay: true,
        };
      }

      if (typeof cellData === "number") {
        return {
          kind: GridCellKind.Number,
          data: cellData,
          displayData: cellData.toString(),
          allowOverlay: true,
          contentAlign: "right",
          thousandSeparator: " ",
        };
      }

      if (typeof cellData === "boolean") {
        return {
          kind: GridCellKind.Boolean,
          data: cellData,
          allowOverlay: false,
        };
      }

      return {
        kind: GridCellKind.Text,
        data: "",
        displayData: "",
        allowOverlay: true,
        readonly: true,
      };
    },
    [data, getRowAndColumnNames, getCellContentFromProps],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellsEdited: DataEditorProps["onCellsEdited"] = (items) => {
    setData(
      produce(data, (draft) => {
        for (const { location, value } of items) {
          const [rowName, columnName] = getRowAndColumnNames(location);
          const newValue = value.data;

          // If transformCellValue callback is provided, it can transform the new value
          // before it's stored. Return undefined to use default handling, or return a custom
          // value to override the cell's new data.
          const customValue = transformCellValue?.(location, newValue, data);

          if (customValue !== undefined) {
            draft[rowName][columnName] = customValue;
          } else if (isValidCellValue(newValue)) {
            draft[rowName][columnName] = newValue;
          }
        }
      }),
    );

    return true;
  };

  const handleGridSelectionChange = (newSelection: GridSelection) => {
    setSelectedRows(newSelection.rows);
  };

  const handleDeleteClick = () => {
    deleteRows(selectedRows.toArray());
  };

  /**
   * Handles deletion requests from the grid (Delete key).
   *
   * @param selection - The selection to delete.
   * @returns What the grid should clear after this handler:
   * - `true`: the contents of all selected cells
   * - `false`: nothing (used here, since rows are deleted manually)
   * - a `GridSelection`: the contents of this selection only
   */
  const handleDelete = (selection: GridSelection) => {
    if (!allowRowDeletion || selection.rows.length === 0) {
      return true;
    }

    deleteRows(selection.rows.toArray());

    return false;
  };

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    // External submit buttons (`form="..."`) bypass disabled inputs
    if (!canEdit) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const changes = getChanges();

    const dataArg: DataGridFormSubmitData<TData> = {
      values: data,
      dirtyValues: changes.updated,
      changes,
      markAsSaved,
    };

    try {
      const submitRes = await onSubmit(dataArg, event);
      setSavedData(data);
      onSubmitSuccessful?.(dataArg, submitRes);
    } catch (err) {
      if (!disableErrorSnackbar) {
        enqueueErrorSnackbar(t("form.submit.error"), toError(err));
      }
      setError(toError(err).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={mergeSxProp(
        {
          display: "flex",
          flexDirection: "column",
          height: 1,
          overflow: "auto",
        },
        sx,
      )}
      component="form"
      id={id}
      onSubmit={handleSubmit}
    >
      <DataGrid
        getCellContent={getCellContent}
        columns={columnsWithAdjustedSize}
        rows={rowNames.length}
        onCellsEdited={handleCellsEdited}
        onGridSelectionChange={handleGridSelectionChange}
        onDelete={handleDelete}
        rowMarkers={rowMarkers}
        isLoading={isLoading}
        readOnly={readOnly || isSubmitting}
        getCellsForSelection
        fillHandle
        allowedFillDirections={allowedFillDirections}
        onPaste
        {...dataGridProps}
      />
      <Stack className="DataGridForm__Footer" direction="column" gap={1.5} sx={{ mt: 1.5 }}>
        {error !== null && (
          <Box color="error.main" sx={{ fontSize: "0.9rem" }}>
            {error || t("form.submit.error")}
          </Box>
        )}
        <Stack gap={1.5}>
          {!hideSubmitButton && (
            <>
              <Button
                type="submit"
                disabled={!canSubmit}
                loading={isSubmitting}
                loadingPosition="start"
                variant="contained"
                startIcon={submitButtonIcon}
              >
                {submitButtonText || t("global.save")}
              </Button>
              <Divider orientation="vertical" flexItem />
            </>
          )}
          <Box>
            <Tooltip title={t("global.undo")}>
              <span>
                <IconButton onClick={undo} disabled={!canUndo}>
                  <UndoIcon />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title={t("global.redo")}>
              <span>
                <IconButton onClick={redo} disabled={!canRedo}>
                  <RedoIcon />
                </IconButton>
              </span>
            </Tooltip>
          </Box>

          {allowRowDeletion && (
            <>
              <Divider orientation="vertical" flexItem />
              <Tooltip title={t("global.delete")}>
                <span>
                  <IconButton onClick={handleDeleteClick} disabled={!canDelete || !hasSelectedRows}>
                    <DeleteIcon />
                  </IconButton>
                </span>
              </Tooltip>
            </>
          )}
          {extraActions && (
            <Box sx={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 1 }}>
              {typeof extraActions === "function" ? extraActions({ canSubmit }) : extraActions}
            </Box>
          )}
        </Stack>
      </Stack>
    </Box>
  );
}

export default DataGridForm;
