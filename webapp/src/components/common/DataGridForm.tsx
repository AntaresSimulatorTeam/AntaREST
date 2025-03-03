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
  GridCellKind,
  type Item,
  type DataEditorProps,
  type GridColumn,
  type FillHandleDirection,
} from "@glideapps/glide-data-grid";
import type { DeepPartial } from "react-hook-form";
import { useCallback, useEffect, useMemo, useState } from "react";
import DataGrid, { type DataGridProps, type RowMarkers } from "./DataGrid";
import { Box, Divider, IconButton, setRef, Tooltip, type SxProps, type Theme } from "@mui/material";
import useUndo, { type Actions } from "use-undo";
import UndoIcon from "@mui/icons-material/Undo";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";
import { mergeSxProp } from "@/utils/muiUtils";
import * as R from "ramda";
import type { SubmitHandlerPlus } from "./Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormCloseProtection from "@/hooks/useCloseFormSecurity";
import { useUpdateEffect } from "react-use";
import { toError } from "@/utils/fnUtils";
import useSafeMemo from "@/hooks/useSafeMemo";
import { getColumnWidth } from "@/utils/dataGridUtils";

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
  allowedFillDirections?: FillHandleDirection;
  enableColumnResize?: boolean;
  onSubmit: (
    data: SubmitHandlerPlus<TData>,
    event?: React.BaseSyntheticEvent,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (data: SubmitHandlerPlus<TData>, submitResult: SubmitReturnValue) => void;
  onStateChange?: (state: DataGridFormState) => void;
  sx?: SxProps<Theme>;
  extraActions?: React.ReactNode;
  apiRef?: React.Ref<DataGridFormApi<TData>>;
}

function DataGridForm<TData extends Data>({
  defaultData,
  columns,
  allowedFillDirections = "vertical",
  enableColumnResize,
  rowMarkers: rowMarkersFromProps,
  onSubmit,
  onSubmitSuccessful,
  onStateChange,
  sx,
  extraActions,
  apiRef,
}: DataGridFormProps<TData>) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedData, setSavedData] = useState(defaultData);
  const [{ present: data }, { set: setData, undo, redo, canUndo, canRedo }] = useUndo(defaultData);

  // Reference comparison to check if the data has changed.
  // So even if the content are the same, we consider it as dirty.
  // Deep comparison fix the issue but with big data it can be slow.
  const isDirty = savedData !== data;

  const formState = useMemo<DataGridFormState>(
    () => ({
      isDirty,
      isSubmitting,
    }),
    [isDirty, isSubmitting],
  );

  useFormCloseProtection({ isSubmitting, isDirty });

  useUpdateEffect(() => onStateChange?.(formState), [formState]);

  useEffect(() => setRef(apiRef, { data, setData, formState }), [apiRef, data, setData, formState]);

  // Rows cannot be added or removed, so no dependencies are needed
  const rowNames = useSafeMemo(() => Object.keys(defaultData), []);

  const columnsWithAdjustedSize = useMemo(
    () =>
      columns.map((column) => ({
        ...column,
        width: getColumnWidth(column, () =>
          rowNames.map((rowName) => defaultData[rowName][column.id].toString()),
        ),
      })),
    [columns, defaultData, rowNames],
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
    }, {} as DeepPartial<TData>);
  };

  ////////////////////////////////////////////////////////////////
  // Content
  ////////////////////////////////////////////////////////////////

  const getCellContent = useCallback<DataEditorProps["getCellContent"]>(
    (location) => {
      const [rowName, columnName] = getRowAndColumnNames(location);
      const dataRow = data[rowName];
      const cellData = dataRow?.[columnName];

      if (typeof cellData == "string") {
        return {
          kind: GridCellKind.Text,
          data: cellData,
          displayData: cellData,
          allowOverlay: true,
        };
      }

      if (typeof cellData == "number") {
        return {
          kind: GridCellKind.Number,
          data: cellData,
          displayData: cellData.toString(),
          allowOverlay: true,
          contentAlign: "right",
          thousandSeparator: " ",
        };
      }

      if (typeof cellData == "boolean") {
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
    [data, getRowAndColumnNames],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellsEdited: DataEditorProps["onCellsEdited"] = (items) => {
    setData(
      items.reduce((acc, { location, value }) => {
        const [rowName, columnName] = getRowAndColumnNames(location);
        const newValue = value.data;

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

    const dataArg = {
      values: data,
      dirtyValues: getDirtyValues(),
    };

    try {
      const submitRes = await onSubmit(dataArg, event);
      setSavedData(data);
      onSubmitSuccessful?.(dataArg, submitRes);
    } catch (err) {
      enqueueErrorSnackbar(t("form.submit.error"), toError(err));
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
        enableColumnResize={enableColumnResize}
        getCellsForSelection
        onPaste
      />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          mt: 1.5,
        }}
      >
        <Box sx={{ display: "flex" }}>
          <LoadingButton
            type="submit"
            disabled={!isDirty}
            loading={isSubmitting}
            loadingPosition="start"
            variant="contained"
            startIcon={<SaveIcon />}
          >
            {t("global.save")}
          </LoadingButton>
          <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />
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
            <Box sx={{ marginLeft: "auto", display: "flex", gap: 1 }}>{extraActions}</Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default DataGridForm;
