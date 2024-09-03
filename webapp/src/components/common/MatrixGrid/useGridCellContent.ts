import { useCallback, useMemo } from "react";
import { GridCell, GridCellKind, Item } from "@glideapps/glide-data-grid";
import { type EnhancedGridColumn, type ColumnType } from "./types";
import { ColumnDataType } from "./utils";

/**
 * Options for formatting date and time strings.
 *
 * Note on Time Zone Handling:
 *
 * The 'timeZone' option is set to "UTC" to ensure consistent date and time
 * representation across different systems and geographical locations. This is
 * crucial for several reasons:
 *
 * 1. Consistency: UTC provides a universal time standard, eliminating
 *    discrepancies caused by daylight saving time or different time zones.
 *
 * 2. Data Integrity: Many systems store timestamps in UTC. By displaying in UTC,
 *    we maintain fidelity to the original data without implicit conversions.
 *
 * 3. Global Applications: For applications used across multiple time zones,
 *    UTC ensures all users see the same time representation.
 *
 * 4. Debugging and Logging: UTC timestamps are easier to compare and analyze,
 *    especially when dealing with events occurring across different time zones.
 *
 * 5. Testing: Using UTC in tests provides consistent results regardless of where
 *    the tests are run, enhancing test reliability and reproducibility.
 *
 */
const dateTimeFormatOptions: Intl.DateTimeFormatOptions = {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
  timeZone: "UTC", // Ensures consistent UTC-based time representation
};

/**
 * Formats a date and time string using predefined locale and format options.
 *
 * This function takes a date/time string, creates a Date object from it,
 * and then formats it according to the specified options. The formatting
 * is done using the French locale as the primary choice, falling back to
 * English if French is not available.
 *
 * Important: This function will always return the time in UTC, regardless
 * of the system's local time zone. This behavior is controlled by the
 * 'timeZone' option in dateTimeFormatOptions.
 *
 * @param dateTime - The date/time string to format. This should be an ISO 8601 string (e.g., "2024-01-01T00:00:00Z").
 * @returns The formatted date/time string in the format specified by dateTimeFormatOptions, always in UTC.
 *
 * @example
 * // returns "1 janv. 2024, 00:00" (assuming French locale is available)
 * formatDateTime("2024-01-01T00:00:00Z")
 *
 * @example
 * // returns "Jan 1, 2024, 00:00" (if French locale is not available)
 * formatDateTime("2024-01-01T00:00:00Z")
 */
function formatDateTime(dateTime: string): string {
  return new Date(dateTime).toLocaleDateString(
    ["fr", "en"], // TODO check if i18n locale switch this if not fix it
    dateTimeFormatOptions,
  );
}

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
  [ColumnDataType.Text]: (
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
  [ColumnDataType.DateTime]: (row, col, column, data, dateTime) => ({
    kind: GridCellKind.Text,
    data: "", // Date/time columns are not editable
    displayData: formatDateTime(dateTime?.[row] ?? ""),
    readonly: !column.editable,
    allowOverlay: false,
  }),
  [ColumnDataType.Number]: (row, col, column, data) => {
    const value = data?.[row]?.[col];

    return {
      kind: GridCellKind.Number,
      data: value,
      displayData: value?.toString(),
      readonly: !column.editable,
      allowOverlay: true,
    };
  },
  [ColumnDataType.Aggregate]: (
    row,
    col,
    column,
    data,
    dateTime,
    aggregates,
  ) => {
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
 * @returns A function that accepts a grid item and returns the configured grid cell content.
 */
export function useGridCellContent(
  data: number[][],
  columns: EnhancedGridColumn[],
  gridToData: (cell: Item) => Item | null,
  dateTime?: string[],
  aggregates?: Record<string, number[]>,
  rowHeaders?: string[],
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

      if (column.type === ColumnDataType.Number && gridToData) {
        // Map grid cell to data array index
        const dataCell = gridToData(cell);

        if (dataCell) {
          adjustedCol = dataCell[0];
        }
      }

      return generator(
        row,
        adjustedCol,
        column,
        data,
        dateTime,
        aggregates,
        rowHeaders,
      );
    },
    [columnMap, data, dateTime, aggregates, rowHeaders, gridToData],
  );

  return getCellContent;
}
