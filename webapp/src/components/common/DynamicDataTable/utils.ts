import { ChipProps } from "@mui/material";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export enum ColumnOperation {
  SUM = "SUM",
  MAX = "MAX",
  MIN = "MIN",
}

type ColumnResult = {
  [key: string]: number;
};

export interface ChipColorMap {
  [key: string]: ChipProps["color"];
}

export interface Column {
  name: string;
  label: string;
  chipColorMap?: ChipColorMap;
  operation?: ColumnOperation;
}

export interface ColumnValues {
  [key: string]: string | number | boolean;
}

export interface Item {
  id: string;
  name: string;
  group?: string;
  columns: ColumnValues;
}

export interface AddItemDialogProps {
  open: boolean;
  onClose: () => void;
  onAddItem: (item: Item) => void;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function performColumnOperation(
  operation: ColumnOperation,
  values: number[],
): number {
  switch (operation) {
    case ColumnOperation.SUM:
      return values.reduce((acc, value) => acc + value, 0);
    case ColumnOperation.MAX:
      return Math.max(...values);
    case ColumnOperation.MIN:
      return Math.min(...values);
    default:
      return 0;
  }
}

export function calculateColumnResults(
  columns: Column[],
  items: Item[],
): ColumnResult {
  const columnResults: ColumnResult = {};

  columns.forEach((column) => {
    if (column.operation) {
      const values = items
        .filter((item) => item.columns[column.name] !== undefined)
        .map((item) => item.columns[column.name]);

      columnResults[column.name] = performColumnOperation(
        column.operation,
        values as number[],
      );
    }
  });

  return columnResults;
}
