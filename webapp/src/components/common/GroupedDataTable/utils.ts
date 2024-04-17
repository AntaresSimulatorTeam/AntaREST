import * as R from "ramda";
import { nameToId } from "../../../services/utils";
import { TableCellProps } from "@mui/material";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface TRow {
  id: string;
  name: string;
  group: string;
}

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
 * @param property - The property for which the unique value is generated, either "name" or "id".
 * @param originalValue - The original value of the specified property.
 * @param tableData - The existing table data to check against for ensuring uniqueness.
 * @returns A unique value for the specified property.
 */
export const generateUniqueValue = (
  property: "name" | "id",
  originalValue: string,
  tableData: TRow[],
): string => {
  let baseValue: string;

  if (property === "name") {
    baseValue = `${originalValue} - copy`;
  } else {
    baseValue = nameToId(originalValue);
  }

  const existingValues = tableData.map((row) => row[property]);
  return generateNextValue(baseValue, existingValues);
};

export function getTableOptionsForAlign(align: TableCellProps["align"]) {
  return {
    muiTableHeadCellProps: { align },
    muiTableBodyCellProps: { align },
    muiTableFooterCellProps: { align },
  };
}
