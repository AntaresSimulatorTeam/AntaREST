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

import type { IdType } from "@/common/types";
import {
  GridCellKind,
  type Item,
  type DataEditorProps,
  type GridColumn,
  type FillHandleDirection,
} from "@glideapps/glide-data-grid";
import type { DeepPartial } from "react-hook-form";
import { FormEvent, useCallback, useState } from "react";
import DataGrid from "./DataGrid";
import {
  Box,
  Divider,
  IconButton,
  SxProps,
  Theme,
  Tooltip,
} from "@mui/material";
import useUndo from "use-undo";
import UndoIcon from "@mui/icons-material/Undo";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";
import { mergeSxProp } from "@/utils/muiUtils";
import * as R from "ramda";
import { SubmitHandlerPlus } from "./Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormCloseProtection from "@/hooks/useCloseFormSecurity";

type GridFieldValuesByRow = Record<
  IdType,
  Record<string, string | boolean | number>
>;

export interface DataGridFormProps<
  TFieldValues extends GridFieldValuesByRow = GridFieldValuesByRow,
  SubmitReturnValue = unknown,
> {
  defaultData: TFieldValues;
  columns: ReadonlyArray<GridColumn & { id: keyof TFieldValues }>;
  allowedFillDirections?: FillHandleDirection;
  onSubmit?: (
    data: SubmitHandlerPlus<TFieldValues>,
    event?: React.BaseSyntheticEvent,
  ) => void | Promise<SubmitReturnValue>;
  onSubmitSuccessful?: (
    data: SubmitHandlerPlus<TFieldValues>,
    submitResult: SubmitReturnValue,
  ) => void;
  sx?: SxProps<Theme>;
  extraActions?: React.ReactNode;
}

function DataGridForm<TFieldValues extends GridFieldValuesByRow>({
  defaultData,
  columns,
  allowedFillDirections = "vertical",
  onSubmit,
  onSubmitSuccessful,
  sx,
  extraActions,
}: DataGridFormProps<TFieldValues>) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedData, setSavedData] = useState(defaultData);
  const [{ present: data }, { set, undo, redo, canUndo, canRedo }] =
    useUndo(defaultData);

  const isSubmitAllowed = savedData !== data;

  useFormCloseProtection({
    isSubmitting,
    isDirty: isSubmitAllowed,
  });

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getRowAndColumnNames = (location: Item) => {
    const [colIndex, rowIndex] = location;
    const rowNames = Object.keys(data);
    const columnIds = columns.map((column) => column.id);

    return [rowNames[rowIndex], columnIds[colIndex]];
  };

  const getDirtyValues = () => {
    return Object.keys(data).reduce((acc, rowName) => {
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
    }, {} as DeepPartial<TFieldValues>);
  };

  ////////////////////////////////////////////////////////////////
  // Callbacks
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
    [data, columns],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellsEdited: DataEditorProps["onCellsEdited"] = (items) => {
    set(
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

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!onSubmit) {
      return;
    }

    setIsSubmitting(true);

    const dataArg = {
      values: data,
      dirtyValues: getDirtyValues(),
    };

    Promise.resolve(onSubmit(dataArg, event))
      .then((submitRes) => {
        setSavedData(data);
        onSubmitSuccessful?.(dataArg, submitRes);
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("form.submit.error"), err);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
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
      onSubmit={handleFormSubmit}
    >
      <DataGrid
        getCellContent={getCellContent}
        columns={columns}
        rows={Object.keys(data).length}
        onCellsEdited={handleCellsEdited}
        rowMarkers={{
          kind: "clickable-string",
          getTitle: (index) => Object.keys(data)[index],
        }}
        fillHandle
        allowedFillDirections={allowedFillDirections}
        getCellsForSelection
      />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          mt: 1.5,
        }}
      >
        <Divider flexItem />
        <Box sx={{ display: "flex" }}>
          <LoadingButton
            type="submit"
            size="small"
            disabled={!isSubmitAllowed}
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
              <IconButton
                size="small"
                onClick={undo}
                disabled={!canUndo || isSubmitting}
              >
                <UndoIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t("global.redo")}>
            <span>
              <IconButton
                size="small"
                onClick={redo}
                disabled={!canRedo || isSubmitting}
              >
                <RedoIcon />
              </IconButton>
            </span>
          </Tooltip>
          {extraActions && (
            <Box sx={{ marginLeft: "auto", display: "flex", gap: 1 }}>
              {extraActions}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default DataGridForm;
