import moment from "moment";
import {
  DateIncrementStrategy,
  EnhancedGridColumn,
  ColumnTypes,
} from "./types";
import { getCurrentLanguage } from "../../../utils/i18nUtils";
import { Theme } from "@glideapps/glide-data-grid";
import { MatrixIndex } from "../../../common/types";

export const darkTheme: Theme = {
  accentColor: "rgba(255, 184, 0, 0.9)",
  accentLight: "rgba(255, 184, 0, 0.2)",
  accentFg: "#FFFFFF",
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
  headerFontStyle: "bold 11px",
  baseFontStyle: "13px",
  fontFamily: "Inter, sans-serif",
  editorFontSize: "13px",
  lineHeight: 1.5,
  textHeaderSelected: "#FFFFFF",
  cellHorizontalPadding: 8,
  cellVerticalPadding: 5,
  headerIconSize: 16,
  markerFontStyle: "normal",
};

export const readOnlyDarkTheme: Partial<Theme> = {
  bgCell: "#1A1C2A",
  bgCellMedium: "#22243A",
  textDark: "#A0A0A0",
  textMedium: "#808080",
  textLight: "#606060",
  accentColor: "#4A4C66",
  accentLight: "rgba(74, 76, 102, 0.2)",
  borderColor: "rgba(255, 255, 255, 0.08)",
  drilldownBorder: "rgba(255, 255, 255, 0.2)",
};

const dateIncrementStrategies: Record<
  MatrixIndex["level"],
  DateIncrementStrategy
> = {
  hourly: (date, step) => date.clone().add(step, "hours"),
  daily: (date, step) => date.clone().add(step, "days"),
  weekly: (date, step) => date.clone().add(step, "weeks"),
  monthly: (date, step) => date.clone().add(step, "months"),
  annual: (date, step) => date.clone().add(step, "years"),
};

const dateTimeFormatOptions: Intl.DateTimeFormatOptions = {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "numeric",
  timeZone: "UTC", // Ensures consistent UTC-based time representation
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

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
 * @example <caption>returns "1 janv. 2024, 00:00" (French locale)</caption>
 * formatDateTime("2024-01-01T00:00:00Z")
 *
 * @example <caption>returns "Jan 1, 2024, 12:00 AM" (English locale)</caption>
 * formatDateTime("2024-01-01T00:00:00Z")
 */
export function formatDateTime(dateTime: string): string {
  const date = moment.utc(dateTime);
  const currentLocale = getCurrentLanguage();
  const locales = [currentLocale, "en-US"];

  return date.toDate().toLocaleString(locales, dateTimeFormatOptions);
}

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
 * @see {@link MatrixIndex} for the structure of the timeMetadata object.
 * @see {@link DateIncrementStrategy} for the date increment strategy type.
 */
export function generateDateTime({
  // eslint-disable-next-line camelcase
  start_date,
  steps,
  level,
}: MatrixIndex): string[] {
  const startDate = moment.utc(start_date, "YYYY-MM-DD HH:mm:ss");
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
 *   { id: "rowHeaders", title: "", type: ColumnTypes.Text, ... },
 *   { id: "date", title: "Date", type: ColumnTypes.DateTime, ... },
 *   ...generateTimeSeriesColumns({ count: 60 }),
 *   { id: "min", title: "Min", type: ColumnTypes.Aggregate, ... },
 *   { id: "max", title: "Max", type: ColumnTypes.Aggregate, ... },
 *   { id: "avg", title: "Avg", type: ColumnTypes.Aggregate, ... }
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
    type: ColumnTypes.Number,
    style: style,
    width: width,
    editable: editable,
  }));
}
