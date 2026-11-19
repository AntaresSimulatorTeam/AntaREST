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
import * as R from "ramda";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useUndo, { type Actions } from "use-undo";
import DataGrid, { type DataGridProps, type DataGridRef, type RowMarkers } from "./DataGrid";
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
  added: Partial<TData>;
  updated: Partial<TData>;
  deleted: Array<keyof TData>;
}

export interface GridSubmitHandlerPlus<TData extends Data = Data> extends SubmitHandlerPlus<TData> {
  /** Row-level changes: added, updated and deleted rows */
  changes: Changes<TData>;
  /**
   * Marks a row as saved as soon as its request succeeds.
   * Useful when `onSubmit` sends several requests: if one fails, the rows
   * already saved won't be included again in the next submit's changes.
   */
  markAsSaved: (rowName: keyof TData) => void;
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
  transformCellValue?: (
    location: Item,
    newValue: unknown,
    data: TData,
  ) => TData[string][keyof TData[string]] | undefined;
  onSubmit: (
    data: GridSubmitHandlerPlus<TData>,
    event: React.SubmitEvent<HTMLFormElement>,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: GridSubmitHandlerPlus<TData>,
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
  const dataGridRef = useRef<DataGridRef>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedData, setSavedData] = useState(defaultData);
  const [error, setError] = useState<string | null>(null);
  const [hasSelectedRows, setHasSelectedRows] = useState(false);

  const [{ present: data }, { set: setData, undo, redo, canUndo: hasUndo, canRedo: hasRedo }] =
    useUndo(defaultData);
  const rowNames = useMemo(() => Object.keys(data), [data]);
  const changes = useMemo(getChanges, [data, savedData]);

  // Compare contents rather than references (`savedData !== data`):
  // `markAsSaved` creates a new `savedData` object for each saved row.
  // After a partially failed submit, `savedData` is therefore never the same
  // object as `data`, even if the user then reverts the unsaved changes,
  // so a reference comparison would keep the form dirty.
  const isDirty =
    Object.keys(changes.added).length > 0 ||
    Object.keys(changes.updated).length > 0 ||
    changes.deleted.length > 0;

  const canEdit = !isSubmitting && !isLoading && !readOnly;
  const canSubmit = isDirty && canEdit;
  const canUndo = hasUndo && canEdit;
  const canRedo = hasRedo && canEdit;
  const canDelete = allowRowDeletion && canEdit;

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
  function getDirtyValues() {
    return rowNames.reduce((acc, rowName) => {
      const rowData = data[rowName];
      const savedRowData = savedData[rowName];

      // Added or deleted row: not an update, handled in`getChanges`
      if (!rowData || !savedRowData) {
        return acc;
      }

      const dirtyColumns = Object.keys(rowData).filter(
        (columnName) => rowData[columnName] !== savedRowData[columnName],
      );

      if (dirtyColumns.length > 0) {
        return {
          ...acc,
          [rowName]: dirtyColumns.reduce(
            (acc, columnName) => ({
              ...acc,
              [columnName]: rowData[columnName],
            }),
            {},
          ),
        };
      }

      return acc;
    }, {} as Partial<TData>);
  }

  /**
   * Computes the row-level changes between the saved data and the current data.
   *
   * @returns An object containing:
   * - `added`: rows that are not in the saved data, with all their values
   * - `updated`: existing rows, with only their modified columns (same as `getDirtyValues`)
   * - `deleted`: names of the rows that are no longer in the current data
   */
  function getChanges(): Changes<TData> {
    const added: Partial<TData> = {};
    const deleted: Array<keyof TData> = [];

    // Row not in saved data → added
    for (const rowName in data) {
      if (!(rowName in savedData)) {
        added[rowName] = data[rowName];
      }
    }

    // Row in saved data but no longer in current data → deleted
    for (const rowName in savedData) {
      if (!(rowName in data)) {
        deleted.push(rowName);
      }
    }

    return {
      added,
      updated: getDirtyValues(),
      deleted,
    };
  }

  /**
   * Marks a row as saved by syncing it in `savedData` with its submitted value.
   *
   * Passed to `onSubmit` for submits that send several requests: if one fails,
   * the rows already saved won't be included again in the next submit's changes.
   *
   * @param rowName - Name of the row whose request succeeded (added, updated or deleted).
   */
  const markAsSaved = (rowName: keyof TData) => {
    // Functional update so successive calls don't overwrite each other
    setSavedData((prev) => {
      const next = { ...prev };
      if (rowName in data) {
        // Added or updated row
        next[rowName] = data[rowName];
      } else {
        // Deleted row
        delete next[rowName];
      }
      return next;
    });
  };

  ////////////////////////////////////////////////////////////////
  // Cells
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
      items.reduce((acc, { location, value }) => {
        const [rowName, columnName] = getRowAndColumnNames(location);
        const newValue = value.data;

        // If transformCellValue callback is provided, it can transform or validate the new value
        // before it's stored. Return undefined to use default handling, or return a custom
        // value to override the cell's new data.
        if (transformCellValue) {
          const customValue = transformCellValue(location, newValue, acc);

          if (customValue !== undefined) {
            return {
              ...acc,
              [rowName]: {
                ...acc[rowName],
                [columnName]: customValue,
              },
            };
          }
        }

        if (R.isNotNil(newValue)) {
          return {
            ...acc,
            [rowName]: {
              ...acc[rowName],
              [columnName]: newValue,
            },
          };
        }

        return acc;
      }, data),
    );

    return true;
  };

  const handleGridSelectionChange = (newSelection: GridSelection) => {
    setHasSelectedRows(newSelection.rows.length > 0);
  };

  const handleDeleteClick = () => {
    dataGridRef.current?.editor?.emit("delete");
  };

  const handleDelete = (selection: GridSelection) => {
    if (!allowRowDeletion) {
      return false;
    }

    const newData = { ...data };

    selection.rows.toArray().forEach((rowIndex) => {
      const rowName = rowNames[rowIndex];
      if (rowName in newData) {
        delete newData[rowName];
      }
    });

    setData(newData);

    return false;
  };

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    setIsSubmitting(true);
    setError(null);

    const dataArg: GridSubmitHandlerPlus<TData> = {
      values: data,
      dirtyValues: getDirtyValues(),
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
      {allowRowDeletion && (
        <Stack className="DataGridForm__Header" direction="column" gap={1.5} sx={{ mb: 1.5 }}>
          <Box>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              size="small"
              disabled={!canDelete || !hasSelectedRows}
              onClick={handleDeleteClick}
            >
              {t("global.delete")}
            </Button>
          </Box>
        </Stack>
      )}
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
        ref={dataGridRef}
        getCellsForSelection
        fillHandle
        onPaste
        {...dataGridProps}
      />
      <Stack className="DataGridForm__Footer" direction="column" gap={1.5} sx={{ mt: 1.5 }}>
        {error !== null && (
          <Box color="error.main" sx={{ fontSize: "0.9rem" }}>
            {error || t("form.submit.error")}
          </Box>
        )}
        <Box sx={{ display: "flex", alignItems: "center" }}>
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
              <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />
            </>
          )}
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
          {extraActions && (
            <Box sx={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 1 }}>
              {typeof extraActions === "function" ? extraActions({ canSubmit }) : extraActions}
            </Box>
          )}
        </Box>
      </Stack>
    </Box>
  );
}

export default DataGridForm;
