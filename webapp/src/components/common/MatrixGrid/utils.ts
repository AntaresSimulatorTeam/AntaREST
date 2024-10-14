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

import {
  EnhancedGridColumn,
  ColumnTypes,
  TimeSeriesColumnOptions,
  CustomColumnOptions,
  MatrixAggregates,
  AggregateType,
  AggregateConfig,
  Aggregates,
  DateIncrementFunction,
  FormatFunction,
  TimeFrequency,
  TimeFrequencyType,
  DateTimeMetadataDTO,
} from "./types";
import {
  type FirstWeekContainsDate,
  parseISO,
  addHours,
  addDays,
  addWeeks,
  addMonths,
  addYears,
  format,
  startOfWeek,
  Locale,
} from "date-fns";
import { fr, enUS } from "date-fns/locale";
import { getCurrentLanguage } from "../../../utils/i18nUtils";
import { Theme } from "@glideapps/glide-data-grid";
import { t } from "i18next";

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

export const aggregatesTheme: Partial<Theme> = {
  bgCell: "#3D3E5F",
  bgCellMedium: "#383A5C",
  textDark: "#FFFFFF",
  fontFamily: "Inter, sans-serif",
  baseFontStyle: "bold 13px",
  editorFontSize: "13px",
  headerFontStyle: "bold 11px",
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Formats a number by adding spaces as thousand separators.
 *
 * @param num - The number to format.
 * @returns The formatted number as a string.
 */
export function formatNumber(num: number | undefined): string {
  if (num === undefined) {
    return "";
  }

  const [integerPart, decimalPart] = num.toString().split(".");

  // Format integer part with thousand separators using a non-regex approach
  const formattedInteger = integerPart
    .split("")
    .reverse()
    .reduce((acc, digit, index) => {
      if (index > 0 && index % 3 === 0) {
        return digit + " " + acc;
      }
      return digit + acc;
    }, "");

  // Return formatted number, preserving decimal part if it exists
  return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
}

function getLocale(): Locale {
  const lang = getCurrentLanguage();
  return lang && lang.startsWith("fr") ? fr : enUS;
}

/**
 * Configuration object for different time frequencies
 *
 * This object defines how to increment and format dates for various time frequencies.
 * The WEEKLY frequency is of particular interest as it implements custom week starts
 * and handles ISO week numbering.
 */
const TIME_FREQUENCY_CONFIG: Record<
  TimeFrequencyType,
  {
    increment: DateIncrementFunction;
    format: FormatFunction;
  }
> = {
  [TimeFrequency.ANNUAL]: {
    increment: addYears,
    format: () => t("global.time.annual"),
  },
  [TimeFrequency.MONTHLY]: {
    increment: addMonths,
    format: (date: Date) => format(date, "MMM", { locale: getLocale() }),
  },
  [TimeFrequency.WEEKLY]: {
    increment: addWeeks,
    format: (date: Date, firstWeekSize: number) => {
      const weekStart = startOfWeek(date, { locale: getLocale() });

      return format(weekStart, `'${t("global.time.weekShort")}' ww`, {
        locale: getLocale(),
        weekStartsOn: firstWeekSize === 1 ? 0 : 1,
        firstWeekContainsDate: firstWeekSize as FirstWeekContainsDate,
      });
    },
  },
  [TimeFrequency.DAILY]: {
    increment: addDays,
    format: (date: Date) => format(date, "EEE d MMM", { locale: getLocale() }),
  },
  [TimeFrequency.HOURLY]: {
    increment: addHours,
    format: (date: Date) =>
      format(date, "EEE d MMM HH:mm", { locale: getLocale() }),
  },
};

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
  width,
  editable = true,
  style = "normal",
}: TimeSeriesColumnOptions): EnhancedGridColumn[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `data${startIndex + index}`,
    title: `${prefix} ${startIndex + index}`,
    type: ColumnTypes.Number,
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
 * @param customColumns.width - The width of each custom column.
 * @returns An array of EnhancedGridColumn objects representing the generated custom columns.
 */
export function generateCustomColumns({
  titles,
  width,
}: CustomColumnOptions): EnhancedGridColumn[] {
  return titles.map((title, index) => ({
    id: `custom${index + 1}`,
    title,
    type: ColumnTypes.Number,
    style: "normal",
    width,
    editable: true,
  }));
}

/**
 * Generates an array of data columns for a matrix grid.
 *
 * @param enableTimeSeriesColumns - A boolean indicating whether to enable time series columns.
 * @param columnCount - The number of columns to generate.
 * @param customColumns - An optional array of custom column titles.
 * @param colWidth - The width of each column.
 * @returns An array of EnhancedGridColumn objects representing the generated data columns.
 */
export function generateDataColumns(
  enableTimeSeriesColumns: boolean,
  columnCount: number,
  customColumns?: string[],
  colWidth?: number,
): EnhancedGridColumn[] {
  // If custom columns are provided, use them
  if (customColumns) {
    return generateCustomColumns({ titles: customColumns, width: colWidth });
  }

  // Else, generate time series columns if enabled
  if (enableTimeSeriesColumns) {
    return generateTimeSeriesColumns({ count: columnCount });
  }

  return [];
}

// TODO add docs + refactor
export function getAggregateTypes(
  aggregateConfig: AggregateConfig,
): AggregateType[] {
  if (aggregateConfig === "stats") {
    return [Aggregates.Avg, Aggregates.Min, Aggregates.Max];
  }

  if (aggregateConfig === "all") {
    return [Aggregates.Min, Aggregates.Max, Aggregates.Avg, Aggregates.Total];
  }

  if (Array.isArray(aggregateConfig)) {
    return aggregateConfig;
  }

  return [];
}

export function calculateMatrixAggregates(
  matrix: number[][],
  aggregateTypes: AggregateType[],
): Partial<MatrixAggregates> {
  const aggregates: Partial<MatrixAggregates> = {};

  matrix.forEach((row) => {
    if (aggregateTypes.includes(Aggregates.Min)) {
      if (!aggregates.min) {
        aggregates.min = [];
      }
      aggregates.min.push(Math.min(...row));
    }

    if (aggregateTypes.includes(Aggregates.Max)) {
      if (!aggregates.max) {
        aggregates.max = [];
      }
      aggregates.max.push(Math.max(...row));
    }

    if (
      aggregateTypes.includes(Aggregates.Avg) ||
      aggregateTypes.includes(Aggregates.Total)
    ) {
      const sum = row.reduce((sum, num) => sum + num, 0);

      if (aggregateTypes.includes(Aggregates.Avg)) {
        if (!aggregates.avg) {
          aggregates.avg = [];
        }

        aggregates.avg.push(Number((sum / row.length).toFixed()));
      }

      if (aggregateTypes.includes(Aggregates.Total)) {
        if (!aggregates.total) {
          aggregates.total = [];
        }

        aggregates.total.push(Number(sum.toFixed()));
      }
    }
  });

  return aggregates;
}
