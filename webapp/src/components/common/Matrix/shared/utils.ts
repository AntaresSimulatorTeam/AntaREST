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

import type {
  DataColumnsConfig,
  ResultColumn,
  EnhancedGridColumn,
  TimeSeriesColumnOptions,
  CustomColumnOptions,
  MatrixAggregates,
  AggregateType,
  AggregateConfig,
  DateTimeMetadataDTO,
  FormatGridNumberOptions,
  ResultColumnsOptions,
} from "./types";
import { parseISO, type Locale } from "date-fns";
import { fr, enUS } from "date-fns/locale";
import { getCurrentLanguage } from "@/utils/i18nUtils";
import { Aggregate, Column, TIME_FREQUENCY_CONFIG } from "./constants";
import { groupHeaderTheme } from "../styles";

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
 * ```
 * @param options - The formatting options
 * @param options.value - The number to format.
 * @param options.maxDecimals - Maximum number of decimal places to show.
 * @returns A formatted string representation of the number with proper separators.
 */
export function formatGridNumber({ value, maxDecimals = 0 }: FormatGridNumberOptions): string {
  if (value === undefined) {
    return "";
  }

  const numValue = Number(value);

  if (isNaN(numValue)) {
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
      if (index > 0 && index % 3 === 0) {
        return digit + " " + acc;
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
  return lang && lang.startsWith("fr") ? fr : enUS;
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
export const generateDateTime = (config: DateTimeMetadataDTO): string[] => {
  // eslint-disable-next-line camelcase
  const { start_date, steps, first_week_size, level } = config;
  const { increment, format } = TIME_FREQUENCY_CONFIG[level];
  const initialDate = parseISO(start_date);

  return Array.from({ length: steps }, (_, index) => {
    const date = increment(initialDate, index);
    return format(date, first_week_size);
  });
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
 * @param config.timeSeriesColumns - A boolean indicating whether to enable time series columns
 * @param config.count - The number of columns to generate
 * @param config.customColumns - An optional array of custom column titles
 * @param config.width - The width of each column
 *
 * @returns An array of EnhancedGridColumn objects representing the generated data columns
 */
export function generateDataColumns({
  timeSeriesColumns,
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
  if (timeSeriesColumns) {
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

/**
 * Calculates matrix aggregates based on the provided matrix and aggregate types.
 *
 * @param matrix - The input matrix of numbers.
 * @param aggregateTypes - The types of aggregates to calculate.
 * @returns An object containing the calculated aggregates.
 */
export function calculateMatrixAggregates(
  matrix: number[][],
  aggregateTypes: AggregateType[],
): Partial<MatrixAggregates> {
  const aggregates: Partial<MatrixAggregates> = {};

  matrix.forEach((row) => {
    if (aggregateTypes.includes(Aggregate.Min)) {
      aggregates.min = aggregates.min || [];
      aggregates.min.push(Math.min(...row));
    }

    if (aggregateTypes.includes(Aggregate.Max)) {
      aggregates.max = aggregates.max || [];
      aggregates.max.push(Math.max(...row));
    }

    if (aggregateTypes.includes(Aggregate.Avg) || aggregateTypes.includes(Aggregate.Total)) {
      const sum = row.reduce((acc, num) => acc + num, 0);

      if (aggregateTypes.includes(Aggregate.Avg)) {
        aggregates.avg = aggregates.avg || [];
        aggregates.avg.push(Number((sum / row.length).toFixed()));
      }

      if (aggregateTypes.includes(Aggregate.Total)) {
        aggregates.total = aggregates.total || [];
        aggregates.total.push(Number(sum.toFixed()));
      }
    }
  });

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
 * @returns Array of EnhancedGridColumn objects with grouping applied
 *
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
 *
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
