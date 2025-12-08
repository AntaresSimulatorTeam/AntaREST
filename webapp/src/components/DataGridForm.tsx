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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormBlocker from "@/hooks/useFormBlocker";
import { getColumnWidth } from "@/utils/dataGridUtils";
import { toError } from "@/utils/fnUtils";
import { mergeSxProp } from "@/utils/muiUtils";
import {
  GridCellKind,
  type DataEditorProps,
  type GridColumn,
  type Item,
} from "@glideapps/glide-data-grid";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import UndoIcon from "@mui/icons-material/Undo";
import {
  Box,
  Button,
  Divider,
  IconButton,
  setRef,
  Tooltip,
  type ButtonProps,
  type SxProps,
  type Theme,
} from "@mui/material";
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
    data: SubmitHandlerPlus<TData>,
    event: React.FormEvent<HTMLFormElement>,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (data: SubmitHandlerPlus<TData>, submitResult: SubmitReturnValue) => void;
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
}

function DataGridForm<TData extends Data>({
  defaultData,
  columns,
  allowedFillDirections = "vertical",
  onRowAppended,
  trailingRowOptions,
  enableColumnResize,
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
}: DataGridFormProps<TData>) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedData, setSavedData] = useState(defaultData);
  const [error, setError] = useState<string | null>(null);
  const [{ present: data }, { set: setData, undo, redo, canUndo, canRedo }] = useUndo(defaultData);

  // Reference comparison to check if the data has changed.
  // So even if the content are the same, we consider it as dirty.
  // Deep comparison fix the issue but with big data it can be slow.
  const isDirty = savedData !== data;
  const canSubmit = isDirty && !isSubmitting;

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

  const rowNames = useMemo(() => Object.keys(data), [data]);

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

  const getDirtyValues = () => {
    return rowNames.reduce((acc, rowName) => {
      const rowData = data[rowName];
      const savedRowData = savedData[rowName];

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

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setIsSubmitting(true);
    setError(null);

    const dataArg = {
      values: data,
      dirtyValues: getDirtyValues(),
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
        rowMarkers={rowMarkers}
        fillHandle
        allowedFillDirections={allowedFillDirections}
        onRowAppended={onRowAppended}
        trailingRowOptions={trailingRowOptions}
        enableColumnResize={enableColumnResize}
        getCellsForSelection
        onPaste
      />
      <Box
        className="DataGridForm__Footer"
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          mt: 1.5,
        }}
      >
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
              <IconButton onClick={undo} disabled={!canUndo || isSubmitting}>
                <UndoIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t("global.redo")}>
            <span>
              <IconButton onClick={redo} disabled={!canRedo || isSubmitting}>
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
      </Box>
    </Box>
  );
}

export default DataGridForm;
