import { useCallback, useMemo } from "react";
import { GridCell, GridCellKind, Item } from "@glideapps/glide-data-grid";
import { type EnhancedGridColumn, type ColumnType, ColumnTypes } from "./types";
import { formatDateTime } from "./utils";

type CellContentGenerator = (
  row: number,
  col: number,
  column: EnhancedGridColumn,
  data: number[][],
  dateTime?: string[],
  aggregates?: Record<string, number[]>,
  rowHeaders?: string[],
) => GridCell;

/**
 * Map of cell content generators for each column type.
 * Each generator function creates the appropriate GridCell based on the column type and data.
 */
const cellContentGenerators: Record<ColumnType, CellContentGenerator> = {
  [ColumnTypes.Text]: (
    row,
    col,
    column,
    data,
    dateTime,
    aggregates,
    rowHeaders,
  ) => ({
    kind: GridCellKind.Text,
    data: "", // Custom row headers are not editable
    displayData: rowHeaders?.[row] ?? "",
    readonly: !column.editable,
    allowOverlay: false,
  }),
  [ColumnTypes.DateTime]: (row, col, column, data, dateTime) => ({
    kind: GridCellKind.Text,
    data: "", // Date/time columns are not editable
    displayData: formatDateTime(dateTime?.[row] ?? ""),
    readonly: !column.editable,
    allowOverlay: false,
  }),
  [ColumnTypes.Number]: (row, col, column, data) => {
    const value = data?.[row]?.[col];

    return {
      kind: GridCellKind.Number,
      data: value,
      displayData: value?.toString(),
      readonly: !column.editable,
      allowOverlay: true,
    };
  },
  [ColumnTypes.Aggregate]: (row, col, column, data, dateTime, aggregates) => {
    const value = aggregates?.[column.id]?.[row];

    return {
      kind: GridCellKind.Number,
      data: value,
      displayData: value?.toString() ?? "",
      readonly: !column.editable,
      allowOverlay: false,
    };
  },
};

/**
 * Custom hook to generate cell content for the DataEditor grid.
 *
 * This hook addresses the challenge of mapping different types of data (numbers, dates, text, aggregates)
 * to the correct columns in a grid, regardless of the column arrangement. It's especially useful when
 * the grid structure is dynamic and may include special columns like row headers or date/time columns
 * that are not part of the main data array.
 *
 * The hook creates a flexible mapping system that:
 * 1. Identifies the type of each column (number, text, date, aggregate).
 * 2. For number columns, maps their position in the grid to their index in the data array.
 * 3. Generates appropriate cell content based on the column type and data source.
 *
 * This approach allows for a dynamic grid structure where columns can be added, removed, or rearranged
 * without needing to modify the underlying data access logic.
 *
 * @param data - The matrix of numerical data, where each sub-array represents a row.
 * @param columns - Array of column configurations.
 * @param gridToData - Optional function to map grid cell coordinates to data array indices.
 * @param dateTime - Optional array of date-time strings for date columns.
 * @param aggregates - Optional object mapping column IDs to arrays of aggregated values.
 * @param rowHeaders - Optional array of row header labels.
 * @param readOnly - Whether the grid is read-only (default is false).
 * @returns A function that accepts a grid item and returns the configured grid cell content.
 */
export function useGridCellContent(
  data: number[][],
  columns: EnhancedGridColumn[],
  gridToData: (cell: Item) => Item | null,
  dateTime?: string[],
  aggregates?: Record<string, number[]>,
  rowHeaders?: string[],
  readOnly = false,
): (cell: Item) => GridCell {
  const columnMap = useMemo(() => {
    return new Map(columns.map((column, index) => [index, column]));
  }, [columns]);

  const getCellContent = useCallback(
    (cell: Item): GridCell => {
      const [col, row] = cell;
      const column = columnMap.get(col);

      if (!column) {
        return {
          kind: GridCellKind.Text,
          data: "",
          displayData: "N/A",
          readonly: true,
          allowOverlay: false,
        };
      }

      const generator = cellContentGenerators[column.type];

      if (!generator) {
        console.error(`No generator found for column type: ${column.type}`);
        return {
          kind: GridCellKind.Text,
          data: "",
          displayData: "Error",
          readonly: true,
          allowOverlay: false,
        };
      }

      // Adjust column index for Number type columns (data columns)
      // This ensures we access the correct index in the data array,
      // accounting for any non-data columns in the grid
      let adjustedCol = col;

      if (column.type === ColumnTypes.Number && gridToData) {
        // Map grid cell to data array index
        const dataCell = gridToData(cell);

        if (dataCell) {
          adjustedCol = dataCell[0];
        }
      }

      const gridCell = generator(
        row,
        adjustedCol,
        column,
        data,
        dateTime,
        aggregates,
        rowHeaders,
      );

      // Prevent updates for read-only grids
      if (readOnly) {
        return {
          ...gridCell,
          allowOverlay: false,
        };
      }

      return gridCell;
    },
    [columnMap, gridToData, data, dateTime, aggregates, rowHeaders, readOnly],
  );

  return getCellContent;
}