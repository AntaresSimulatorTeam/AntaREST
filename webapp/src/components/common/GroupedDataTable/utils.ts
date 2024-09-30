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

import * as R from "ramda";
import { TableCellProps } from "@mui/material";
import type { TRow } from "./types";

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Generates the next unique value based on a base value and a list of existing values.
 * If the base value is found in the list of existing values, it appends a number
 * in the format `(n)` to the base value, incrementing `n` until a unique value is found.
 *
 * @param baseValue - The original base value to check for uniqueness.
 * @param existingValues - The list of existing values to check against for duplicates.
 * @returns A unique value derived from the base value by appending a number in parentheses, if necessary.
 */
export const generateNextValue = (
  baseValue: string,
  existingValues: string[],
): string => {
  const pattern = new RegExp(`^${baseValue}( \\(\\d+\\))?`);
  const matchingValues = R.filter(
    (value) => pattern.test(value),
    existingValues,
  );

  if (matchingValues.length === 0) {
    return baseValue;
  }

  const maxCount = R.pipe(
    R.map((value: string) => {
      const match = value.match(/\((\d+)\)$/);
      return match ? parseInt(match[1], 10) : 0;
    }),
    R.reduce(R.max, 0),
  )(matchingValues);

  return `${baseValue} (${Number(maxCount) + 1})`;
};

/**
 * Generates a unique value for a specified property ('name' or 'id')
 * based on the given original value and the existing values in tableData.
 *
 * If the property is "name", the function appends " - copy" to the original value.
 * If the property is "id", the function uses `nameToId` to get the base value.
 *
 * This function leverages `generateNextValue` to ensure the uniqueness of the value.
 *
 * @param originalValue - The original value of the specified property.
 * @param tableData - The existing table data to check against for ensuring uniqueness.
 * @returns A unique value for the specified property.
 */
export const generateUniqueValue = (
  originalValue: string,
  tableData: TRow[],
): string => {
  const existingValues = tableData.map((row) => row.name);
  return generateNextValue(`${originalValue} - copy`, existingValues);
};

export function getTableOptionsForAlign(align: TableCellProps["align"]) {
  return {
    muiTableHeadCellProps: { align },
    muiTableBodyCellProps: { align },
    muiTableFooterCellProps: { align },
  };
}
