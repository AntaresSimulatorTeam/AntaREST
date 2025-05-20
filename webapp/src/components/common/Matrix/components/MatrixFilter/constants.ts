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

export const FILTER_TYPES = {
  RANGE: "range",
  LIST: "list",
};

export const TIME_INDEXING = {
  DAY_OF_MONTH: "dayOfMonth",
  DAY_OF_YEAR: "dayOfYear",
  DAY_HOUR: "dayHour",
  HOUR_YEAR: "hourYear",
  MONTH: "month",
  WEEK: "week",
  WEEKDAY: "weekday",
};

// Maps time frequency to appropriate indexing options
export const TIME_FREQUENCY_INDEXING_MAP: Record<TimeFrequencyType, string[]> = {
  [TimeFrequency.Annual]: [TIME_INDEXING.MONTH], // Annual data typically just uses sequential indices
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
};

// Get default indexing type based on time frequency
export const getDefaultIndexingType = (timeFrequency?: TimeFrequencyType): string => {
  if (!timeFrequency) {
    return TIME_INDEXING.DAY_OF_MONTH;
  }

  const options = TIME_FREQUENCY_INDEXING_MAP[timeFrequency];
  return options && options.length > 0 ? options[0] : TIME_INDEXING.DAY_OF_MONTH;
};

export const TEMPORAL_OPTIONS: TemporalOption[] = [
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
];

export const createDefaultRowFilter = (
  rowCount: number,
  timeFrequency?: TimeFrequencyType,
): RowFilter => ({
  id: crypto.randomUUID(),
  indexingType: getDefaultIndexingType(timeFrequency),
  type: FILTER_TYPES.RANGE,
  range: { min: 1, max: rowCount || 1 },
  list: [],
});

export const getDefaultFilterState = (
  rowCount: number,
  columnCount: number,
  timeFrequency?: TimeFrequencyType,
): FilterState => ({
  active: false,
  columnsFilter: {
    type: FILTER_TYPES.RANGE,
    range: { min: 1, max: Math.max(columnCount, 1) },
    list: [],
  },
  rowsFilters: [createDefaultRowFilter(rowCount, timeFrequency)],
  operation: {
    type: Operation.Eq,
    value: 0,
  },
});
