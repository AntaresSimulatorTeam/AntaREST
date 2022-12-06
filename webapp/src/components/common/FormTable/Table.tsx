import HotTable from "@handsontable/react";
import type { RowObject } from "handsontable/common";
import * as RA from "ramda-adjunct";
import { useMemo } from "react";
import type { IdType } from "../../../common/types";
import { useFormContextPlus } from "../Form";
import Handsontable, { HandsontableProps } from "../Handsontable";

type Row = { id: IdType } & RowObject;

export interface TableProps extends Omit<HandsontableProps, "rowHeaders"> {
  data: Row[];
  columns: NonNullable<HandsontableProps["columns"]>;
  rowHeaders?: boolean | ((row: Row) => string);
  tableRef?: React.ForwardedRef<HotTable>;
}

function Table(props: TableProps) {
  const {
    data,
    rowHeaders = (row: Row) => String(row.id),
    tableRef,
    ...restProps
  } = props;
  const { setValue } = useFormContextPlus();

  const rowHeaderWidth = useMemo(
    () =>
      RA.isBoolean(rowHeaders)
        ? undefined
        : data.reduce(
            (longestHeaderLength, row) => {
              const headerLength = rowHeaders(row).length;

              return longestHeaderLength > headerLength
                ? longestHeaderLength
                : headerLength;
            },
            3 // To force minimum size
          ) * 8,
    [data, rowHeaders]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAfterChange: HandsontableProps["afterChange"] =
    function afterChange(this: unknown, changes, ...rest): void {
      changes?.forEach(([row, column, _, nextValue]) => {
        setValue(`${data[row].id}.${column}`, nextValue);
      });
      restProps.afterChange?.call(this, changes, ...rest);
    };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Handsontable
      allowInvalid={false}
      allowEmpty={false}
      rowHeaderWidth={rowHeaderWidth}
      manualColumnResize
      manualRowResize
      {...restProps}
      data={data}
      rowHeaders={
        RA.isFunction(rowHeaders)
          ? (index) => rowHeaders(data[index])
          : rowHeaders
      }
      afterChange={handleAfterChange}
      ref={tableRef}
    />
  );
}

export default Table;
