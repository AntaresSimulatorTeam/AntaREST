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

/* eslint-disable camelcase */
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

import { UTCDate } from "@date-fns/utc";
import type { Locale } from "date-fns";
import { enUS, fr } from "date-fns/locale";
import { getCurrentLanguage } from "@/utils/i18nUtils";
import { groupHeaderTheme } from "../styles";
import { Aggregate, Column, TIME_FREQUENCY_CONFIG } from "./constants";
import type {
  AggregateConfig,
  AggregateType,
  CalculateAggregatesParams,
  CustomColumnOptions,
  DataColumnsConfig,
  DateTimeMetadataDTO,
  DateTimes,
  EnhancedGridColumn,
  FormatGridNumberOptions,
  MatrixAggregates,
  ResizeMatrixParams,
  ResultColumn,
  ResultColumnsOptions,
  TimeSeriesColumnOptions,
} from "./types";

/**
 * Formats a number for display in a grid cell by adding thousand separators and handling decimals.
 *
 * This function is particularly useful for displaying load factors,
 * which are numbers between 0 and 1. For load factors, a maximum of
 * 6 decimal places should be displayed. For statistics, a maximum of
 * 3 decimal places is recommended.
 *
 * @example
 * ```typescript
 * formatGridNumber({ value: 1234567.89, maxDecimals: 2 }) // "1 234 567.89"
 * formatGridNumber({ value: 0, maxDecimals: 6 }) // "0"
 * formatGridNumber({ value: undefined }) // ""
 * formatGridNumber({ value: NaN }) // ""
 * formatGridNumber({ value: "1234.56", maxDecimals: 1 }) // "1 234.5"
 * ```
 * @param options - The formatting options
 * @param options.value - The number or numeric string to format.
 * @param options.maxDecimals - Maximum number of decimal places to show.
 * @returns A formatted string representation of the number with proper separators.
 */
export function formatGridNumber({ value, maxDecimals = 0 }: FormatGridNumberOptions): string {
  if (value === undefined) {
    return "";
  }

  const numValue = Number(value);

  if (Number.isNaN(numValue)) {
    return "";
  }

  const stringValue = value.toString();
  const dotIndex = stringValue.indexOf(".");
  const hasDecimals = dotIndex !== -1;
  const shouldFormatDecimals =
    hasDecimals && maxDecimals > 0 && stringValue.length - dotIndex - 1 > maxDecimals;

  const formattedValue = shouldFormatDecimals ? numValue.toFixed(maxDecimals) : stringValue;

  const [integerPart, decimalPart] = formattedValue.split(".");

  const formattedInteger = integerPart
    .split("")
    .reverse()
    .reduce((acc, digit, index) => {
      // Intentionally add space as thousand separator
      // Example: "1234567" becomes "1 234 567"
      if (index > 0 && index % 3 === 0) {
        return `${digit} ${acc}`;
      }
      return digit + acc;
    }, "");

  return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
}

/**
 * Retrieves the current locale based on the user's language setting.
 *
 * @returns  Returns either the French (fr) or English US (enUS) locale object
 * depending on whether the current language starts with "fr"
 */
export function getLocale(): Locale {
  const lang = getCurrentLanguage();
  return lang?.startsWith("fr") ? fr : enUS;
}

/**
 * Generates an array of formatted date/time strings based on the provided configuration
 *
 * This function handles various time frequencies, with special attention to weekly formatting.
 * For weekly frequency, it respects custom week starts while maintaining ISO week numbering.
 *
 * @param config - Configuration object for date/time generation
 * @param config.start_date - The starting date for generation
 * @param config.steps - Number of increments to generate
 * @param config.first_week_size - Defines the number of days for the first the week (from 1 to 7)
 * @param config.level - The time frequency level (ANNUAL, MONTHLY, WEEKLY, DAILY, HOURLY)
 * @returns An array of formatted date/time strings
 */
export const generateDateTime = (config: DateTimeMetadataDTO): DateTimes => {
  const { start_date, steps, first_week_size, level } = config;
  const { increment } = TIME_FREQUENCY_CONFIG[level];

  /**
   * TIMEZONE DETECTION BUG FIX:
   *
   * Previously, we used a naive approach to detect timezone information:
   *   start_date.includes("Z") || start_date.includes("+") || start_date.includes("-")
   *
   * This caused a critical bug where date strings like "2018-01-01 00:00:00"
   * were incorrectly identified as having timezone info because they contain
   * "-" characters in the date part (2018-01-01).
   *
   * Result: The "Z" suffix wasn't appended, causing dates to be interpreted
   * in local timezone instead of UTC, leading to:
   * - "2018-01-01 00:00:00" → "2017-12-31T23:00:00.000Z" in UTC+1
   * - Display showed "Sun 31 Dec 23:00" instead of "Mon 1 Jan 00:00"
   *
   * SOLUTION:
   * Use a regex that only matches timezone indicators at the END of the string:
   * - /[Z]$/ matches "Z" at the end
   * - /[+-]\d{2}:?\d{2}$/ matches "+HH:MM", "+HHMM", "-HH:MM", "-HHMM" at the end
   *
   * This ensures date separators like "2018-01-01" are not mistaken for timezone info.
   */
  const timezoneRegex = /[Z]$|[+-]\d{2}:?\d{2}$/;
  const hasTimezone = timezoneRegex.test(start_date);

  // Append 'Z' to indicate UTC if no timezone is specified
  const dateStr = hasTimezone ? start_date : `${start_date}Z`;

  const initialDate = new UTCDate(dateStr);

  const values = Array.from({ length: steps }, (_, index) => increment(initialDate, index));
  return { values, first_week_size, level };
};

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
 *   { id: "rowHeaders", title: "", type: Column.Text, ... },
 *   { id: "date", title: "Date", type: Column.DateTime, ... },
 *   ...generateTimeSeriesColumns({ count: 60 }),
 *   { id: "min", title: "Min", type: Column.Aggregate, ... },
 *   { id: "max", title: "Max", type: Column.Aggregate, ... },
 *   { id: "avg", title: "Avg", type: Column.Aggregate, ... }
 * ];
 */
export function generateTimeSeriesColumns({
  count,
  startIndex = 1,
  prefix = "TS",
  width,
  editable = true,
  style = "normal",
}: TimeSeriesColumnOptions): EnhancedGridColumn[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `data${startIndex + index}`,
    title: `${prefix} ${startIndex + index}`,
    type: Column.Number,
    style,
    width,
    editable,
  }));
}

/**
 * Generates custom columns for a matrix grid.
 *
 * @param customColumns - An array of strings representing the custom column titles.
 * @param customColumns.titles - The titles of the custom columns.
 * @param customColumns.width - The width of each column.
 * @returns An array of EnhancedGridColumn objects representing the generated custom columns.
 */
export function generateCustomColumns({
  titles,
  width,
}: CustomColumnOptions): EnhancedGridColumn[] {
  return titles.map((title, index) => ({
    id: `custom${index + 1}`,
    title,
    width,
    type: Column.Number,
    editable: true,
  }));
}

/**
 * Generates an array of data columns for a matrix grid.
 *
 * @param config - Configuration object for generating columns
 * @param config.isTimeSeries - A boolean indicating whether to enable time series columns
 * @param config.count - The number of columns to generate
 * @param config.customColumns - An optional array of custom column titles
 * @param config.width - The width of each column
 * @returns An array of EnhancedGridColumn objects representing the generated data columns
 */
export function generateDataColumns({
  isTimeSeries,
  width,
  count,
  customColumns,
}: DataColumnsConfig): EnhancedGridColumn[] {
  // If custom columns are provided, use them
  if (customColumns) {
    return generateCustomColumns({
      titles: customColumns,
      width,
    });
  }

  // Else, generate time series columns if enabled
  if (isTimeSeries) {
    return generateTimeSeriesColumns({
      count,
    });
  }

  return [];
}

/**
 * Determines the aggregate types based on the provided configuration.
 *
 * @param aggregateConfig - The configuration for aggregates.
 * @returns An array of AggregateType.
 */
export function getAggregateTypes(aggregateConfig: AggregateConfig): AggregateType[] {
  if (aggregateConfig === "stats") {
    return [Aggregate.Avg, Aggregate.Min, Aggregate.Max];
  }

  if (aggregateConfig === "all") {
    return [Aggregate.Min, Aggregate.Max, Aggregate.Avg, Aggregate.Total];
  }

  if (Array.isArray(aggregateConfig)) {
    return aggregateConfig;
  }

  return [];
}

export function calculateMatrixAggregates({
  matrix,
  types,
}: CalculateAggregatesParams): Partial<MatrixAggregates> {
  const aggregates: Partial<MatrixAggregates> = {};

  for (const row of matrix) {
    if (types.includes(Aggregate.Min)) {
      aggregates.min ??= [];
      aggregates.min.push(Math.min(...row));
    }

    if (types.includes(Aggregate.Max)) {
      aggregates.max ??= [];
      aggregates.max.push(Math.max(...row));
    }

    if (types.includes(Aggregate.Avg) || types.includes(Aggregate.Total)) {
      const sum = row.reduce((acc, num) => acc + num, 0);

      if (types.includes(Aggregate.Avg)) {
        aggregates.avg ??= [];
        aggregates.avg.push(Number((sum / row.length).toFixed()));
      }

      if (types.includes(Aggregate.Total)) {
        aggregates.total ??= [];
        aggregates.total.push(Number(sum.toFixed()));
      }
    }
  }

  return aggregates;
}

/**
 * Creates grouped columns specifically for result matrices by processing title arrays.
 *
 * This function expects columns with titles in a specific array format [variable, unit, stat]:
 * - Position 1: Variable name (e.g., "OV. COST")
 * - Position 2: Unit (e.g., "Euro", "MW")
 * - Position 3: Statistic type (e.g., "MIN", "MAX", "STD")
 *
 * Example of expected title format:
 * ```typescript
 * {
 *   id: "custom1",
 *   title: ["OV. COST", "Euro", "MIN"],  // [variable, unit, stat]
 *   type: "number",
 *   editable: true
 * }
 * ```
 *
 * !Important: Do not use outside of results matrices.
 * This function relies on array positions to determine meaning.
 * It assumes the API provides data in the correct format:
 * - titles[0] will always be the variable name
 * - titles[1] will always be the unit
 * - titles[2] will always be the statistic type
 * This makes the solution fragile to API changes.
 *
 * @param columns - Array of EnhancedGridColumn objects to be processed
 * @param isDarkMode - Boolean flag based on the theme to switch columns group headers color
 * @returns Array of EnhancedGridColumn objects with grouping applied
 * @example
 * ```typescript
 * // Input columns
 * const columns = [
 *   { id: "col1", title: ["OV. COST", "Euro", "MIN"], type: "number", editable: true },
 *   { id: "col2", title: ["OV. COST", "Euro", "MAX"], type: "number", editable: true }
 * ];
 * // Both columns will be grouped under "OV. COST (Euro)"
 * ```
 */
export function groupResultColumns(
  columns: Array<EnhancedGridColumn | ResultColumn>,
  isDarkMode: boolean,
): EnhancedGridColumn[] {
  return columns.map((column): EnhancedGridColumn => {
    const titles = Array.isArray(column.title) ? column.title : [String(column.title)];

    // Extract and validate components
    // [0]: Variable name (e.g., "OV. COST")
    // [1]: Unit (e.g., "Euro")
    // [2]: Statistic type (e.g., "MIN", "MAX", "STD")
    const [variable, unit, stat] = titles.map((t) => String(t).trim());

    // Create group name:
    // - If unit exists and is not empty/whitespace, add it in parentheses
    // - If no unit or empty unit, use variable name alone
    const hasUnit = unit && unit.trim().length > 0;
    const title = hasUnit ? `${variable} (${unit})` : variable;

    // If no stats, it does not make sense to group columns
    if (!stat) {
      return {
        ...column,
        title,
      };
    }

    return {
      ...column,
      group: title, // Group header title
      title: stat.toLowerCase(), // Sub columns title,
      themeOverride: isDarkMode ? groupHeaderTheme.dark : groupHeaderTheme.light,
    };
  });
}

/**
 * Generates an array of ResultColumn objects from a 2D array of column titles.
 * Each title array should follow the format [variable, unit, stat] as used in result matrices.
 * This function is designed to work in conjunction with groupResultColumns()
 * to create properly formatted and grouped result matrix columns.
 *
 * @param titles - 2D array of string arrays, where each inner array contains:
 *   - [0]: Variable name (e.g., "OV. COST")
 *   - [1]: Unit (e.g., "Euro", "MW")
 *   - [2]: Statistic type (e.g., "MIN", "MAX", "STD")
 * @param width - The width of each column
 * @returns Array of ResultColumn objects ready for use in result matrices
 * @see groupResultColumns - Use this function to apply grouping to the generated columns
 */

export function generateResultColumns({ titles, width }: ResultColumnsOptions): ResultColumn[] {
  return titles.map((title, index) => ({
    id: `custom${index + 1}`,
    title,
    type: Column.Number,
    width,
    editable: false,
  }));
}

/**
 * Resizes each row of the given matrix to the specified number of columns.
 *
 * For each row in the matrix:
 * - If the row has fewer columns than the target count, new columns are appended with the provided fill value.
 * - If the row has more columns than the target count, the row is truncated to the target count.
 *
 * @param params - The parameters for resizing the matrix.
 * @param params.matrix - The original matrix to resize, where each row is a non-empty array.
 * @param params.newColumnCount - The desired number of columns for each row.
 * @param [params.fillValue=0] - The value to fill in new columns if the row needs to be extended. Defaults to 0.
 * @returns A new matrix where every row has exactly `newColumnCount` columns.
 */
export function resizeMatrix({ matrix, newColumnCount, fillValue = 0 }: ResizeMatrixParams) {
  return matrix.map((row) => {
    const currentColumnCount = row.length;

    // Add new columns
    if (newColumnCount > currentColumnCount) {
      return row.concat(Array(newColumnCount - currentColumnCount).fill(fillValue));
    }

    // Otherwise remove the extra columns
    if (newColumnCount < currentColumnCount) {
      return row.slice(0, newColumnCount);
    }

    return row;
  });
}
