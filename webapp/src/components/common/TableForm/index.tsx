import * as RA from "ramda-adjunct";
import { ColumnSettings } from "handsontable/settings";
import { startCase } from "lodash";
import * as R from "ramda";
import { Box, type SxProps } from "@mui/material";
import type { Theme } from "@mui/system";
import { useMemo } from "react";
import { DefaultValues } from "react-hook-form";
import type { IdType } from "../../../common/types";
import Form, { FormProps } from "../Form";
import Table, { TableProps } from "./Table";
import { getCellType } from "./utils";
import { mergeSxProp } from "../../../utils/muiUtils";
import useMemoLocked from "../../../hooks/useMemoLocked";

type TableFieldValuesByRow = Record<
  IdType,
  Record<string, string | boolean | number>
>;

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
    columns?:
      | Array<string | ColumnSettings>
      | ((index: number) => ColumnSettings);
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
  const defaultData = useMemoLocked(() =>
    R.keys(defaultValues).map((id) => ({
      ...defaultValues[id],
      id: id as IdType,
    })),
  );

  const formattedColumns = useMemo(() => {
    if (!columns || Array.isArray(columns)) {
      const firstRow = defaultData[0];
      const cols = columns || Object.keys(R.omit(["id"], firstRow));

      return cols.map(
        (col, index): ColumnSettings =>
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
        <Table
          data={defaultData}
          columns={formattedColumns}
          {...restTableProps}
        />
      </Box>
    </Form>
  );
}

export default TableForm;
