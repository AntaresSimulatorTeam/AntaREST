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

import * as RA from "ramda-adjunct";
import type HT from "handsontable";
import startCase from "lodash/startCase";
import * as R from "ramda";
import { Box, type SxProps, type Theme } from "@mui/material";
import { useMemo } from "react";
import type { DefaultValues } from "react-hook-form";
import type { IdType } from "../../../types/types";
import Form, { type FormProps } from "../Form";
import Table, { type TableProps } from "./Table";
import { getCellType } from "./utils";
import { mergeSxProp } from "../../../utils/muiUtils";
import useSafeMemo from "../../../hooks/useSafeMemo";

type TableFieldValuesByRow = Record<IdType, Record<string, string | boolean | number>>;

export interface TableFormProps<
  TFieldValues extends TableFieldValuesByRow = TableFieldValuesByRow,
> {
  defaultValues: DefaultValues<TFieldValues>;
  onSubmit?: FormProps<TFieldValues>["onSubmit"];
  onInvalid?: FormProps<TFieldValues>["onInvalid"];
  autoSubmit?: FormProps<TFieldValues>["autoSubmit"];
  enableUndoRedo?: FormProps<TFieldValues>["enableUndoRedo"];
  formApiRef?: FormProps<TFieldValues>["apiRef"];
  sx?: SxProps<Theme>;
  tableProps?: Omit<TableProps, "data" | "columns" | "colHeaders"> & {
    columns?: Array<string | HT.ColumnSettings> | ((index: number) => HT.ColumnSettings);
    colHeaders?: (index: number, colName: string) => string;
  };
}

function TableForm<TFieldValues extends TableFieldValuesByRow>(
  props: TableFormProps<TFieldValues>,
) {
  const {
    defaultValues,
    onSubmit,
    onInvalid,
    autoSubmit = true, // TODO: change to false after testing all table forms
    enableUndoRedo,
    sx,
    formApiRef,
    tableProps = {},
  } = props;

  const { columns, type, colHeaders, ...restTableProps } = tableProps;

  // useForm's defaultValues are cached on the first render within the custom hook.
  const defaultData = useSafeMemo(
    () =>
      R.keys(defaultValues).map((id) => ({
        ...defaultValues[id],
        id: id as IdType,
      })),
    [],
  );

  const formattedColumns = useMemo(() => {
    if (!columns || Array.isArray(columns)) {
      const firstRow = defaultData[0];
      const cols = columns || Object.keys(R.omit(["id"], firstRow));

      return cols.map(
        (col, index): HT.ColumnSettings =>
          RA.isString(col)
            ? {
                data: col,
                title: colHeaders ? colHeaders(index, col) : startCase(col),
                type: type || getCellType(firstRow?.[col]),
              }
            : col,
      );
    }
    return columns;
  }, [columns, defaultData, colHeaders, type]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      config={{ defaultValues }}
      onSubmit={onSubmit}
      onInvalid={onInvalid}
      autoSubmit={autoSubmit}
      enableUndoRedo={enableUndoRedo}
      sx={mergeSxProp(
        {
          width: 1,
          height: 1,
          display: "flex",
          flexDirection: "column",
        },
        sx,
      )}
      apiRef={formApiRef}
    >
      <Box
        sx={{
          // https://handsontable.com/docs/12.0/grid-size/#define-the-size-in-css-styles
          overflow: "auto",
        }}
      >
        <Table data={defaultData} columns={formattedColumns} {...restTableProps} />
      </Box>
    </Form>
  );
}

export default TableForm;
