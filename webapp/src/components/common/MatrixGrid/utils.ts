import moment from "moment";
import {
  TimeMetadataDTO,
  DateIncrementStrategy,
  EnhancedGridColumn,
} from "./types";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export const ColumnDataType = {
  DateTime: "datetime",
  Number: "number",
  Text: "text",
  Aggregate: "aggregate",
} as const;

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

const dateIncrementStrategies: Record<
  TimeMetadataDTO["level"],
  DateIncrementStrategy
> = {
  hourly: (date, step) => date.clone().add(step, "hours"),
  daily: (date, step) => date.clone().add(step, "days"),
  weekly: (date, step) => date.clone().add(step, "weeks"),
  monthly: (date, step) => date.clone().add(step, "months"),
  yearly: (date, step) => date.clone().add(step, "years"),
};

export const darkTheme = {
  accentColor: "#6366F1",
  accentFg: "#FFFFFF",
  accentLight: "rgba(99, 102, 241, 0.2)",
  textDark: "#FFFFFF",
  textMedium: "#C1C3D9",
  textLight: "#A1A5B9",
  textBubble: "#FFFFFF",
  bgIconHeader: "#1E1F2E",
  fgIconHeader: "#FFFFFF",
  textHeader: "#FFFFFF",
  textGroupHeader: "#C1C3D9",
  bgCell: "#262737", // main background color
  bgCellMedium: "#2E2F42",
  bgHeader: "#1E1F2E",
  bgHeaderHasFocus: "#2E2F42",
  bgHeaderHovered: "#333447",
  bgBubble: "#333447",
  bgBubbleSelected: "#3C3E57",
  bgSearchResult: "#6366F133",
  borderColor: "rgba(255, 255, 255, 0.12)",
  drilldownBorder: "rgba(255, 255, 255, 0.35)",
  linkColor: "#818CF8",
  headerFontStyle: "bold 13px",
  baseFontStyle: "13px",
  fontFamily: "Inter, sans-serif",
  editorFontSize: "13px",
  lineHeight: 1.5,
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Generates an array of date-time strings based on the provided time metadata.
 *
 * This function creates a series of date-time strings, starting from the given start date
 * and incrementing based on the specified level (hourly, daily, weekly, monthly, or yearly).
 * It uses the Moment.js library for date manipulation and the ISO 8601 format for date-time strings.
 *
 * @param timeMetadata - The time metadata object.
 * @param timeMetadata.start_date - The starting date-time in ISO 8601 format (e.g., "2023-01-01T00:00:00Z").
 * @param timeMetadata.steps - The number of date-time strings to generate.
 * @param timeMetadata.level - The increment level for date-time generation.
 *
 * @returns An array of ISO 8601 formatted date-time strings.
 *
 * @example
 * const result = generateDateTime({
 *   start_date: "2023-01-01T00:00:00Z",
 *   steps: 3,
 *   level: "daily"
 * });
 *
 *  Returns: [
 *    "2023-01-01T00:00:00.000Z",
 *    "2023-01-02T00:00:00.000Z",
 *    "2023-01-03T00:00:00.000Z"
 *  ]
 *
 * @see {@link TimeMetadataDTO} for the structure of the timeMetadata object.
 * @see {@link DateIncrementStrategy} for the date increment strategy type.
 */
export function generateDateTime({
  // eslint-disable-next-line camelcase
  start_date,
  steps,
  level,
}: TimeMetadataDTO): string[] {
  const startDate = moment(start_date);
  const incrementStrategy = dateIncrementStrategies[level];

  return Array.from({ length: steps }, (_, i) =>
    incrementStrategy(startDate, i).toISOString(),
  );
}

/**
 * Generates an array of EnhancedGridColumn objects representing time series data columns.
 *
 * @param options - The options for generating time series columns.
 * @param options.count - The number of time series columns to generate.
 * @param [options.startIndex=1] - The starting index for the time series columns (default is 1).
 * @param [options.prefix="TS"] - The prefix to use for the column titles (default is "TS").
 * @param [options.width=50] - The width of each column (default is 50).
 * @param [options.editable=true] - Whether the columns should be editable (default is true).
 * @param [options.style="normal"] - The style of the columns (default is "normal").
 * @returns An array of EnhancedGridColumn objects representing time series data columns.
 *
 * @example <caption>Usage within a column definition array</caption>
 * const columns = [
 *   { id: "rowHeaders", title: "", type: ColumnDataType.Text, ... },
 *   { id: "date", title: "Date", type: ColumnDataType.DateTime, ... },
 *   ...generateTimeSeriesColumns({ count: 60 }),
 *   { id: "min", title: "Min", type: ColumnDataType.Aggregate, ... },
 *   { id: "max", title: "Max", type: ColumnDataType.Aggregate, ... },
 *   { id: "avg", title: "Avg", type: ColumnDataType.Aggregate, ... }
 * ];
 */
export function generateTimeSeriesColumns({
  count,
  startIndex = 1,
  prefix = "TS",
  width = 50,
  editable = true,
  style = "normal",
}: {
  count: number;
  startIndex?: number;
  prefix?: string;
  width?: number;
  editable?: boolean;
  style?: "normal" | "highlight";
}): EnhancedGridColumn[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `data${startIndex + index}`,
    title: `${prefix} ${startIndex + index}`,
    type: ColumnDataType.Number,
    style: style,
    width: width,
    editable: editable,
  }));
}
