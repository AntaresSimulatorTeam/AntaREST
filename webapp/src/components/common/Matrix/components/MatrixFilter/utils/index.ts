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

import type { TFunction } from "i18next";
import * as R from "ramda";
import { TimeFrequency } from "../../../shared/constants";
import type { DateTimes, TimeFrequencyType } from "../../../shared/types";
import {
  FILTER_OPERATORS,
  FILTER_TYPES,
  TIME_FREQUENCY_INDEXING_MAP,
  TIME_INDEXING,
} from "../constants";
import type {
  FilterState,
  IndexedValue,
  RowFilter,
  SliderMark,
  TemporalIndexingParams,
  TemporalOption,
} from "../types";
import { extractValueFromDate, getLocalizedTimeLabels } from "./dateUtils";

const createRowIndices = R.memoizeWith(
  (size: number) => String(size),
  (size: number) => R.range(0, size),
);

/**
 * Combines multiple filter results using OR logic (union) - includes all indices from any filter
 *
 * @param results
 */
const combineFilterResultsOR = R.pipe<[number[][]], number[], number[], number[]>(
  R.flatten,
  R.uniq,
  R.sort(R.subtract),
);

/**
 * Combines multiple filter results using AND logic (intersection) - includes only indices present in all filters
 *
 * @param results - Array of arrays containing row indices
 * @returns the combined filter results
 */
const combineFilterResultsAND = (results: number[][]): number[] => {
  if (results.length === 0) {
    return [];
  }

  if (results.length === 1) {
    return results[0];
  }

  // Start with the first result and intersect with each subsequent result
  return R.pipe(
    R.reduce<number[], number[]>(R.intersection, results[0]),
    R.sort(R.subtract),
  )(results.slice(1));
};

/**
 * Gets all row indices using memoized Ramda range
 *
 * @param totalRows
 */
const getAllRowIndices = createRowIndices;

/**
 * Safely extracts matrix dimensions
 *
 * @param matrixData - The 2D array of numbers to extract dimensions from
 * @returns An object containing the row count and column count of the matrix
 */
export function getMatrixDimensions(matrixData: number[][]): {
  rowCount: number;
  columnCount: number;
} {
  return {
    rowCount: matrixData.length,
    columnCount: matrixData[0]?.length || 0,
  };
}

/**
 * Creates an array of indexed values using Ramda
 *
 * @param count
 */
const createIndexedValues = R.memoizeWith(
  (count: number) => String(count),
  (count: number): IndexedValue[] => R.times((i) => ({ index: i, value: i + 1 }), count),
);

/**
 * Extracts temporal indices from date/time data based on filter configuration
 *
 * @param props - The temporal indexing parameters object
 * @param props.rowFilter - The row filter configuration to apply
 * @param props.dateTime - Array of date/time strings for temporal indexing
 * @param props.isTimeSeries - Whether the data represents a time series
 * @param props.timeFrequency - The time frequency of the data
 * @param props.totalRows - Total number of rows in the dataset
 * @returns Array of row indices that match the filter criteria
 */
export function getTemporalIndices({
  rowFilter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  totalRows,
}: TemporalIndexingParams): number[] {
  // Use simple indices for non-time series data
  if (!isTimeSeries || !dateTime?.values.length) {
    const indices = createIndexedValues(totalRows);
    return applyRowFilter(rowFilter, indices, totalRows);
  }

  // Extract temporal values from date strings
  const temporalIndices = dateTime.values
    .map((date, index) => {
      if (timeFrequency === TimeFrequency.Annual) {
        return { index, value: index + 1 };
      }

      try {
        const value = extractValueFromDate(date, rowFilter.indexingType);
        return { index, value };
      } catch {
        // Skip invalid dates
        return null;
      }
    })
    .filter((item): item is IndexedValue => item !== null);

  return applyRowFilter(rowFilter, temporalIndices, totalRows);
}

/**
 * Applies filter logic to indexed values
 *
 * @param rowFilter - The row filter configuration to apply
 * @param indices - Array of indexed values to filter
 * @param totalRows - Total number of rows in the dataset
 * @returns Array of filtered row indices
 */
function applyRowFilter(
  rowFilter: RowFilter,
  indices: IndexedValue[],
  totalRows: number,
): number[] {
  const filteredIndices = filterByType(rowFilter, indices);

  return R.pipe(
    R.map<IndexedValue, number>(R.prop("index")),
    R.filter(R.both(R.gte(R.__, 0), R.lt(R.__, totalRows))),
  )(filteredIndices);
}

/**
 * Filters indices based on filter type and configuration
 *
 * @param rowFilter - The row filter configuration to apply
 * @param indices - Array of indexed values to filter
 * @returns Filtered array of indexed values
 */
function filterByType(rowFilter: RowFilter, indices: IndexedValue[]): IndexedValue[] {
  if (rowFilter.type === FILTER_TYPES.RANGE && rowFilter.range) {
    const { min, max } = rowFilter.range;

    return R.filter((item: IndexedValue) => {
      const value = item.value;
      return value >= min && value <= max;
    }, indices);
  }

  if (rowFilter.type === FILTER_TYPES.LIST) {
    return filterByList(rowFilter, indices);
  }

  return indices;
}

/**
 * Applies list-based filtering with operator support
 *
 * @param rowFilter - The row filter configuration containing operator and list values
 * @param indices - Array of indexed values to filter
 * @returns Filtered array of indexed values based on the operator and list criteria
 */
function filterByList(rowFilter: RowFilter, indices: IndexedValue[]): IndexedValue[] {
  const operator = rowFilter.operator || FILTER_OPERATORS.EQUALS;
  const list = rowFilter.list || [];

  if (R.isEmpty(list)) {
    return indices;
  }

  const getValue = (item: IndexedValue): number => item.value;

  // Define predicates for each operator
  const predicates: Record<string, (item: IndexedValue) => boolean> = {
    [FILTER_OPERATORS.EQUALS]: (item) => list.includes(getValue(item)),
    [FILTER_OPERATORS.GREATER_THAN]: (item) => getValue(item) > Math.min(...list),
    [FILTER_OPERATORS.LESS_THAN]: (item) => getValue(item) < Math.max(...list),
    [FILTER_OPERATORS.GREATER_EQUAL]: (item) => getValue(item) >= Math.min(...list),
    [FILTER_OPERATORS.LESS_EQUAL]: (item) => getValue(item) <= Math.max(...list),
    [FILTER_OPERATORS.RANGE]:
      list.length >= 2
        ? (item) => {
            const value = getValue(item);
            return value >= Math.min(...list) && value <= Math.max(...list);
          }
        : (item) => list.includes(getValue(item)),
  };

  const predicate = predicates[operator] || predicates[FILTER_OPERATORS.EQUALS];
  return R.filter(predicate, indices);
}

/**
 * Filters temporal options based on time frequency compatibility
 *
 * @param timeFrequency - The time frequency to filter options by
 * @param options - Array of temporal options to filter
 * @returns Filtered array of temporal options compatible with the time frequency
 */
export function getFilteredTemporalOptions(
  timeFrequency: string | undefined,
  options: readonly TemporalOption[],
): TemporalOption[] {
  if (!timeFrequency) {
    return [...options];
  }

  const validOptions = TIME_FREQUENCY_INDEXING_MAP[timeFrequency as TimeFrequencyType];

  if (!validOptions?.length) {
    return [...options];
  }

  return options.filter((option) => validOptions.includes(option.value));
}

/**
 * Processes multiple row filters and combines their results
 * Applies OR logic within filters of the same indexingType
 * Applies AND logic between different indexingTypes
 *
 * @param filter - The filter state containing row filters configuration
 * @param dateTime - Array of date/time strings for temporal indexing
 * @param isTimeSeries - Whether the data represents a time series
 * @param timeFrequency - The time frequency of the data
 * @param totalRows - Total number of rows in the dataset
 * @returns Array of row indices that match the combined filter criteria
 */
export function processRowFilters(
  filter: FilterState,
  dateTime: DateTimes | undefined,
  isTimeSeries: boolean,
  timeFrequency: TimeFrequencyType | undefined,
  totalRows: number,
): number[] {
  const { rowsFilters } = filter;

  // Return all indices if no filters defined
  if (!rowsFilters?.length) {
    return getAllRowIndices(totalRows);
  }

  // Optimize single filter case
  if (rowsFilters.length === 1) {
    return getTemporalIndices({
      filter,
      rowFilter: rowsFilters[0],
      dateTime,
      isTimeSeries,
      timeFrequency,
      totalRows,
    });
  }

  const filtersByType = R.groupBy((rowFilter: RowFilter) => rowFilter.indexingType, rowsFilters);

  // Process each group: apply OR within group
  const groupResults = Object.entries(filtersByType).map(([, filters]) => {
    const filterResults = filters.map((rowFilter) =>
      getTemporalIndices({
        filter,
        rowFilter,
        dateTime,
        isTimeSeries,
        timeFrequency,
        totalRows,
      }),
    );

    // Apply OR logic within the same indexingType group
    return combineFilterResultsOR(filterResults);
  });

  // Apply AND logic between different groups
  return combineFilterResultsAND(groupResults);
}

/**
 * Creates slider marks based on the indexing type
 *
 * @param indexingType - The type of time indexing (e.g., MONTH, WEEKDAY, DAY_HOUR)
 * @param t - Translation function for localizing labels
 * @returns An array of slider marks with values and labels appropriate for the indexing type
 */
export function createSliderMarks(indexingType: string, t: TFunction): SliderMark[] {
  switch (indexingType) {
    case TIME_INDEXING.MONTH: {
      const months = getLocalizedTimeLabels("month", t);
      return months.map(({ value, shortLabel }) => ({
        value,
        label: shortLabel.charAt(0),
      }));
    }

    case TIME_INDEXING.WEEKDAY: {
      const weekdays = getLocalizedTimeLabels("weekday", t);
      return weekdays.map(({ value, shortLabel }) => ({
        value,
        label: shortLabel.charAt(0),
      }));
    }

    case TIME_INDEXING.DAY_HOUR:
      return Array.from({ length: 24 }, (_, i) => ({
        value: i + 1,
        label: (i + 1).toString(),
      }));

    case TIME_INDEXING.DAY_OF_YEAR:
      return [
        { value: 1, label: "1" },
        { value: 31, label: "31" },
        { value: 59, label: "59" },
        { value: 90, label: "90" },
        { value: 120, label: "120" },
        { value: 151, label: "151" },
        { value: 181, label: "181" },
        { value: 212, label: "212" },
        { value: 243, label: "243" },
        { value: 273, label: "273" },
        { value: 304, label: "304" },
        { value: 334, label: "334" },
        { value: 365, label: "365" },
      ];

    case TIME_INDEXING.HOUR_YEAR:
      // TODO: use the existing localized i18n keys for months names
      return [
        { value: 1, label: "Jan" },
        { value: 744, label: "Feb" },
        { value: 1416, label: "Mar" },
        { value: 2160, label: "Apr" },
        { value: 2880, label: "May" },
        { value: 3624, label: "Jun" },
        { value: 4344, label: "Jul" },
        { value: 5088, label: "Aug" },
        { value: 5832, label: "Sep" },
        { value: 6552, label: "Oct" },
        { value: 7296, label: "Nov" },
        { value: 8016, label: "Dec" },
        { value: 8760, label: "Dec 31" },
      ];

    case TIME_INDEXING.DAY_OF_MONTH:
      return [1, 5, 10, 15, 20, 25, 31].map((value) => ({
        value,
        label: value.toString(),
      }));

    case TIME_INDEXING.WEEK:
      return [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 53].map((value) => ({
        value,
        label: value.toString(),
      }));

    default:
      return [];
  }
}

/**
 * Parses a string input into an array of numbers representing a range.
 *
 * @param input - The input string to parse.
 * @returns An array of numbers representing the parsed range.
 */
export function parseRangeInput(input: string): number[] {
  const trimmed = input.trim();

  // Check if input contains a range (e.g., "8-100", "5 - 10")
  const rangeMatch = trimmed.match(/^(\d+)\s*-\s*(\d+)$/);
  if (rangeMatch) {
    const start = Number.parseInt(rangeMatch[1], 10);
    const end = Number.parseInt(rangeMatch[2], 10);
    if (!Number.isNaN(start) && !Number.isNaN(end) && start <= end) {
      return Array.from({ length: end - start + 1 }, (_, i) => start + i);
    }
  }

  // Check for comma-separated values
  const values = trimmed
    .split(",")
    .map((v) => {
      const num = Number.parseInt(v.trim(), 10);
      return Number.isNaN(num) ? null : num;
    })
    .filter((v) => v !== null) as number[];

  return values;
}
