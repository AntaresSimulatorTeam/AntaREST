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

import { Operation, TimeFrequency } from "../../shared/constants";
import type { TimeFrequencyType } from "../../shared/types";
import type { FilterState, RowFilter, TemporalOption, TimeIndexingType } from "./types";

export const FILTER_TYPES = {
  RANGE: "range",
  LIST: "list",
} as const;

export const FILTER_OPERATORS = {
  EQUALS: "equals",
  GREATER_THAN: "greaterThan",
  LESS_THAN: "lessThan",
  GREATER_EQUAL: "greaterEqual",
  LESS_EQUAL: "lessEqual",
  RANGE: "range",
} as const;

export const TIME_INDEXING = {
  DAY_OF_MONTH: "dayOfMonth",
  DAY_OF_YEAR: "dayOfYear",
  DAY_HOUR: "dayHour",
  HOUR_YEAR: "hourYear",
  MONTH: "month",
  WEEK: "week",
  WEEKDAY: "weekday",
} as const;

/**
 * Maps time frequency to appropriate indexing options.
 * Each frequency has its most relevant temporal indexing types ordered by relevance.
 */
export const TIME_FREQUENCY_INDEXING_MAP: Record<TimeFrequencyType, TimeIndexingType[]> = {
  [TimeFrequency.Annual]: [], // No temporal subdivisions make sense for annual data
  [TimeFrequency.Monthly]: [TIME_INDEXING.MONTH],
  [TimeFrequency.Weekly]: [TIME_INDEXING.WEEK, TIME_INDEXING.WEEKDAY, TIME_INDEXING.DAY_OF_MONTH],
  [TimeFrequency.Daily]: [
    TIME_INDEXING.DAY_OF_MONTH,
    TIME_INDEXING.DAY_OF_YEAR,
    TIME_INDEXING.WEEKDAY,
    TIME_INDEXING.WEEK,
    TIME_INDEXING.MONTH,
  ],
  [TimeFrequency.Hourly]: [
    TIME_INDEXING.HOUR_YEAR,
    TIME_INDEXING.WEEK,
    TIME_INDEXING.WEEKDAY,
    TIME_INDEXING.MONTH,
    TIME_INDEXING.DAY_OF_MONTH,
    TIME_INDEXING.DAY_HOUR,
  ],
} as const;

/**
 * Gets the default indexing type for a given time frequency.
 * Returns the first (most relevant) indexing type for the frequency.
 *
 * @param timeFrequency - The time frequency to get default indexing for
 * @returns The default time indexing type
 */
export const getDefaultIndexingType = (timeFrequency?: TimeFrequencyType): TimeIndexingType => {
  if (!timeFrequency) {
    return TIME_INDEXING.DAY_OF_MONTH;
  }

  const options = TIME_FREQUENCY_INDEXING_MAP[timeFrequency];
  return options?.[0] ?? TIME_INDEXING.DAY_OF_MONTH;
};

/**
 * Temporal filtering options with localization keys and descriptions.
 * Each option defines a specific way to filter time-based data.
 */
export const TEMPORAL_OPTIONS: ReadonlyArray<Readonly<TemporalOption>> = [
  {
    value: TIME_INDEXING.DAY_OF_MONTH,
    label: "matrix.filter.indexing.dayOfMonth",
  },
  {
    value: TIME_INDEXING.MONTH,
    label: "matrix.filter.indexing.month",
  },
  {
    value: TIME_INDEXING.WEEKDAY,
    label: "matrix.filter.indexing.weekday",
  },
  {
    value: TIME_INDEXING.DAY_HOUR,
    label: "matrix.filter.indexing.dayHour",
  },
  {
    value: TIME_INDEXING.WEEK,
    label: "matrix.filter.indexing.week",
  },
  {
    value: TIME_INDEXING.DAY_OF_YEAR,
    label: "matrix.filter.indexing.dayOfYear",
  },
  {
    value: TIME_INDEXING.HOUR_YEAR,
    label: "matrix.filter.indexing.hourYear",
  },
];

/**
 * Creates a default row filter configuration.
 * Initializes with appropriate defaults based on data dimensions and time frequency.
 *
 * @param rowCount - The number of rows in the matrix
 * @param timeFrequency - The time frequency for temporal filtering
 * @returns A default row filter configuration
 */
export const createDefaultRowFilter = (
  rowCount: number,
  timeFrequency?: TimeFrequencyType,
): RowFilter => {
  const indexingType = getDefaultIndexingType(timeFrequency);

  return {
    id: crypto.randomUUID(),
    indexingType,
    type: FILTER_TYPES.LIST,
    range: {
      min: 1,
      max: Math.max(rowCount, 1),
    },
    list: [],
    operator: FILTER_OPERATORS.EQUALS,
  };
};

/**
 * Creates the default filter state for the matrix.
 * Initializes all filter components with safe defaults based on matrix dimensions.
 *
 * @param rowCount - The number of rows in the matrix
 * @param columnCount - The number of columns in the matrix
 * @param timeFrequency - The time frequency for temporal filtering
 * @returns The default filter state
 */
export const getDefaultFilterState = (
  rowCount: number,
  columnCount: number,
  timeFrequency?: TimeFrequencyType,
): FilterState => ({
  active: false,
  columnsFilter: {
    type: FILTER_TYPES.LIST,
    range: {
      min: 1,
      max: Math.max(columnCount, 1),
    },
    list: [],
    operator: FILTER_OPERATORS.EQUALS,
  },
  rowsFilters: [createDefaultRowFilter(rowCount, timeFrequency)],
  operation: {
    type: Operation.Eq,
    value: 0,
  },
});
