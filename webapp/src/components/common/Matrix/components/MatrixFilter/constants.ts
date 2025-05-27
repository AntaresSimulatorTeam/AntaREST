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

import { TimeFrequency, Operation } from "../../shared/constants";
import type { FilterState, TemporalOption, RowFilter } from "./types";
import type { TimeFrequencyType } from "../../shared/types";

// Filter type constants
export const FILTER_TYPES = {
  RANGE: "range",
  LIST: "list",
} as const;

export type FilterType = (typeof FILTER_TYPES)[keyof typeof FILTER_TYPES];

// Time indexing type constants
export const TIME_INDEXING = {
  DAY_OF_MONTH: "dayOfMonth",
  DAY_OF_YEAR: "dayOfYear",
  DAY_HOUR: "dayHour",
  HOUR_YEAR: "hourYear",
  MONTH: "month",
  WEEK: "week",
  WEEKDAY: "weekday",
} as const;

export type TimeIndexingType = (typeof TIME_INDEXING)[keyof typeof TIME_INDEXING];

/**
 * Maps time frequency to appropriate indexing options.
 * Each frequency has its most relevant temporal indexing types ordered by relevance.
 */
export const TIME_FREQUENCY_INDEXING_MAP: Record<TimeFrequencyType, readonly TimeIndexingType[]> = {
  [TimeFrequency.Annual]: [TIME_INDEXING.MONTH],
  [TimeFrequency.Monthly]: [TIME_INDEXING.MONTH],
  [TimeFrequency.Weekly]: [TIME_INDEXING.WEEK, TIME_INDEXING.WEEKDAY],
  [TimeFrequency.Daily]: [
    TIME_INDEXING.DAY_OF_MONTH,
    TIME_INDEXING.DAY_OF_YEAR,
    TIME_INDEXING.WEEKDAY,
    TIME_INDEXING.MONTH,
  ],
  [TimeFrequency.Hourly]: [
    TIME_INDEXING.DAY_HOUR,
    TIME_INDEXING.HOUR_YEAR,
    TIME_INDEXING.DAY_OF_MONTH,
    TIME_INDEXING.WEEKDAY,
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
export const TEMPORAL_OPTIONS: readonly TemporalOption[] = [
  {
    value: TIME_INDEXING.DAY_OF_MONTH,
    label: "matrix.filter.indexing.dayOfMonth",
    description: "Filter by day of month (1-31)",
  },
  {
    value: TIME_INDEXING.MONTH,
    label: "matrix.filter.indexing.month",
    description: "Filter by month (1-12)",
  },
  {
    value: TIME_INDEXING.WEEKDAY,
    label: "matrix.filter.indexing.weekday",
    description: "Filter by weekday (1-7, Monday to Sunday)",
  },
  {
    value: TIME_INDEXING.DAY_HOUR,
    label: "matrix.filter.indexing.dayHour",
    description: "Filter by hour of day (1-24)",
  },
  {
    value: TIME_INDEXING.WEEK,
    label: "matrix.filter.indexing.week",
    description: "Filter by week of year (1-53)",
  },
  {
    value: TIME_INDEXING.DAY_OF_YEAR,
    label: "matrix.filter.indexing.dayOfYear",
    description: "Filter by day of year (1-366)",
  },
  {
    value: TIME_INDEXING.HOUR_YEAR,
    label: "matrix.filter.indexing.hourYear",
    description: "Filter by hour of year (1-8760)",
  },
] as const;

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
): RowFilter => ({
  id: crypto.randomUUID(), // TODO: check if necessary to keep, if so use UUID or useId()
  indexingType: getDefaultIndexingType(timeFrequency),
  type: FILTER_TYPES.RANGE,
  range: {
    min: 1,
    max: Math.max(rowCount, 1),
  },
  list: [],
});

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
    type: FILTER_TYPES.RANGE,
    range: {
      min: 1,
      max: Math.max(columnCount, 1),
    },
    list: [],
  },
  rowsFilters: [createDefaultRowFilter(rowCount, timeFrequency)],
  operation: {
    type: Operation.Eq,
    value: 0,
  },
});
