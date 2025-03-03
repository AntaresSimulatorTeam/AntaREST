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

import type HT from "handsontable";
import * as RA from "ramda-adjunct";
import { useMemo } from "react";
import type { IdType } from "../../../types/types";
import { useFormContextPlus } from "../Form";
import Handsontable, { type HandsontableProps, type HotTableClass } from "../Handsontable";

type Row = { id: IdType } & HT.RowObject;

export interface TableProps extends Omit<HandsontableProps, "rowHeaders"> {
  data: Row[];
  columns: NonNullable<HandsontableProps["columns"]>;
  rowHeaders?: boolean | ((row: Row) => string);
  tableRef?: React.ForwardedRef<HotTableClass>;
}

function Table(props: TableProps) {
  const { data, rowHeaders = (row: Row) => String(row.id), tableRef, ...restProps } = props;

  const { setValues } = useFormContextPlus();

  const rowHeaderWidth = useMemo(
    () =>
      RA.isBoolean(rowHeaders)
        ? undefined
        : data.reduce(
            (longestHeaderLength, row) => {
              const headerLength = rowHeaders(row).length;

              return longestHeaderLength > headerLength ? longestHeaderLength : headerLength;
            },
            10, // To force minimum size
          ) * 8,
    [data, rowHeaders],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAfterChange: HandsontableProps["afterChange"] = function afterChange(
    this: unknown,
    changes,
    ...rest
  ): void {
    const newValues = changes?.reduce(
      (acc, [row, column, _, nextValue]) => {
        acc[`${data[row].id}.${column}`] = nextValue;
        return acc;
      },
      {} as Record<string, unknown>,
    );

    if (newValues) {
      setValues(newValues);
    }

    restProps.afterChange?.call(this, changes, ...rest);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Handsontable
      height="auto"
      allowInvalid={false}
      allowEmpty={false}
      rowHeaderWidth={rowHeaderWidth}
      manualColumnResize
      manualRowResize
      {...restProps}
      data={data}
      rowHeaders={RA.isFunction(rowHeaders) ? (index) => rowHeaders(data[index]) : rowHeaders}
      afterChange={handleAfterChange}
      ref={tableRef}
    />
  );
}

export default Table;
