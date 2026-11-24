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

import type { TableCellProps } from "@mui/material";
import type { MRT_TableOptions } from "material-react-table";
import * as R from "ramda";
import type { RowData } from "./types";

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
export const generateNextValue = (baseValue: string, existingValues: string[]): string => {
  const pattern = new RegExp(`^${baseValue}( \\(\\d+\\))?`);
  const matchingValues = R.filter((value) => pattern.test(value), existingValues);

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
export const generateUniqueValue = (originalValue: string, tableData: RowData[]): string => {
  const existingValues = tableData.map((row) => row.name);
  return generateNextValue(`${originalValue} - copy`, existingValues);
};

export function getTableOptionsForAlign(align: TableCellProps["align"]) {
  return {
    muiTableHeadCellProps: { align },
    muiTableBodyCellProps: { align },
    muiTableFooterCellProps: { align },
  } satisfies Partial<MRT_TableOptions<RowData>>;
}

/**
 * Generates styles to fix dark mode issues in Material React Table.
 *
 * Material React Table doesn't apply dark mode styles correctly since MUI v7.
 *
 * @param isDarkMode - A boolean indicating whether dark mode is enabled.
 * @returns An object containing MRT theme overrides and MUI table props
 * with custom styles for dark mode.
 */
export function getDarkModeFixStyles(isDarkMode: boolean) {
  return {
    mrtTheme: isDarkMode
      ? {
          baseBackgroundColor: "#1f2530",
          selectedRowBackgroundColor: "#ffc10733",
        }
      : undefined,
    muiTableProps: {
      sx: (theme) =>
        theme.applyStyles("dark", {
          ".MuiTableRow-root": {
            "&:not(.Mui-selected):hover td:after": {
              backgroundColor: "#62666e4d",
            },
            ".MuiTableSortLabel-icon": {
              fill: "#fff",
            },
          },
        }),
    },
  } satisfies Partial<MRT_TableOptions<RowData>>;
}
