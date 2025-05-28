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

import { FILTER_TYPES, TIME_FREQUENCY_INDEXING_MAP, FILTER_OPERATORS } from "./constants";
import type { FilterState, TemporalIndexingParams, TemporalOption, RowFilter } from "./types";
import { TimeFrequency } from "../../shared/constants";
import type { TimeFrequencyType } from "../../shared/types";
import { extractValueFromDate } from "./dateUtils";

export function getTemporalIndices({
  filter,
  rowFilter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  totalRows,
}: TemporalIndexingParams): number[] {
  // If not time series or no date data, use simple row indices
  if (!isTimeSeries || !dateTime || dateTime.length === 0) {
    return applyRowFilter(
      rowFilter,
      Array.from({ length: totalRows }, (_, i) => ({ index: i, value: i + 1 })),
      totalRows,
    );
  }

  // Extract temporal indices using our utility function
  const timeIndices = dateTime.map((dateStr, index) => {
    const { indexingType } = rowFilter;

    // Handle annual frequency differently
    if (timeFrequency === TimeFrequency.Annual) {
      // For annual data, we typically just use the index as is
      return { index, value: index + 1 };
    }

    // Use the utility function to extract the appropriate value
    const value = extractValueFromDate(dateStr, indexingType, index);
    return { index, value };
  });

  // Apply filter to temporal indices
  return applyRowFilter(rowFilter, timeIndices, totalRows);
}

function applyRowFilter(
  rowFilter: RowFilter,
  indices: Array<{ index: number; value: number }>,
  totalRows: number,
): number[] {
  // Apply filter based on type
  let matchingIndices: typeof indices = [];

  if (rowFilter.type === FILTER_TYPES.RANGE && rowFilter.range) {
    const { min, max } = rowFilter.range;
    matchingIndices = indices.filter(({ value }) => value >= min && value <= max);
  } else if (rowFilter.type === FILTER_TYPES.LIST) {
    const operator = rowFilter.operator || FILTER_OPERATORS.EQUALS;
    const list = rowFilter.list || [];

    if (list.length === 0) {
      matchingIndices = [];
    } else {
      switch (operator) {
        case FILTER_OPERATORS.EQUALS:
          matchingIndices = indices.filter(({ value }) => list.includes(value));
          break;
        case FILTER_OPERATORS.GREATER_THAN: {
          const gtThreshold = Math.min(...list);
          matchingIndices = indices.filter(({ value }) => value > gtThreshold);
          break;
        }
        case FILTER_OPERATORS.LESS_THAN: {
          const ltThreshold = Math.max(...list);
          matchingIndices = indices.filter(({ value }) => value < ltThreshold);
          break;
        }
        case FILTER_OPERATORS.GREATER_EQUAL: {
          const gteThreshold = Math.min(...list);
          matchingIndices = indices.filter(({ value }) => value >= gteThreshold);
          break;
        }
        case FILTER_OPERATORS.LESS_EQUAL: {
          const lteThreshold = Math.max(...list);
          matchingIndices = indices.filter(({ value }) => value <= lteThreshold);
          break;
        }
        case FILTER_OPERATORS.RANGE:
          // For range operator, treat the list as individual values to include
          matchingIndices = indices.filter(({ value }) => list.includes(value));
          break;
        default:
          matchingIndices = indices.filter(({ value }) => list.includes(value));
      }
    }
  } else {
    // Default to all indices
    matchingIndices = indices;
  }

  // Return the row indices (not the temporal values)
  return matchingIndices.map(({ index }) => index).filter((idx) => idx >= 0 && idx < totalRows);
}

/**
 * Filter the temporal options based on time frequency
 *
 * @param timeFrequency - The time frequency of the matrix
 * @param options - The full list of temporal options
 * @returns The filtered list of temporal options valid for the given time frequency
 */
export function getFilteredTemporalOptions(
  timeFrequency: string | undefined,
  options: TemporalOption[],
): TemporalOption[] {
  if (!timeFrequency) {
    return options;
  }

  const validOptions =
    TIME_FREQUENCY_INDEXING_MAP[timeFrequency as keyof typeof TIME_FREQUENCY_INDEXING_MAP] || [];

  if (validOptions.length === 0) {
    return options;
  }

  return options.filter((option) => validOptions.includes(option.value));
}

/**
 * Processes all row filters and returns the combined set of matching row indices
 *
 * @param filter - The filter state containing all row filters
 * @param dateTime - Array of date/time strings
 * @param isTimeSeries - Whether the data is a time series
 * @param timeFrequency - The frequency of the time data
 * @param totalRows - Total number of rows in the matrix
 * @returns Array of row indices that match ANY of the row filters (using OR logic between filters)
 */
export function processRowFilters(
  filter: FilterState,
  dateTime: string[] | undefined,
  isTimeSeries: boolean,
  timeFrequency: TimeFrequencyType | undefined,
  totalRows: number,
): number[] {
  // If no row filters, return all rows
  if (!filter.rowsFilters || filter.rowsFilters.length === 0) {
    return Array.from({ length: totalRows }, (_, i) => i);
  }

  // Process each row filter and collect matching indices
  const allIndices = new Set<number>();

  for (const rowFilter of filter.rowsFilters) {
    const indices = getTemporalIndices({
      filter,
      rowFilter,
      dateTime,
      isTimeSeries,
      timeFrequency,
      totalRows,
    });

    // Add all matching indices to the set
    for (const index of indices) {
      allIndices.add(index);
    }
  }

  // Convert set back to array and sort
  return Array.from(allIndices).sort((a, b) => a - b);
}

/**
 * Safely extracts matrix dimensions from matrix data
 *
 * @param matrixData - The matrix data array
 * @returns Object containing rowCount and columnCount
 */
export function getMatrixDimensions(matrixData: number[][]): {
  rowCount: number;
  columnCount: number;
} {
  const rowCount = matrixData.length;
  const columnCount = matrixData[0]?.length || 0;

  return { rowCount, columnCount };
}

/**
 * Validates that matrix data is properly formatted
 *
 * @param matrixData - The matrix data array to validate
 * @returns Boolean indicating if the matrix is valid
 */
export function isValidMatrix(matrixData: unknown): matrixData is number[][] {
  if (!Array.isArray(matrixData) || matrixData.length === 0) {
    return false;
  }

  const firstRowLength = matrixData[0]?.length;
  if (typeof firstRowLength !== "number") {
    return false;
  }

  return matrixData.every(
    (row) =>
      Array.isArray(row) &&
      row.length === firstRowLength &&
      row.every((cell) => typeof cell === "number"),
  );
}

/**
 * Creates default indices arrays for given dimensions
 *
 * @param rowCount - Number of rows
 * @param columnCount - Number of columns
 * @returns Object containing rowsIndices and columnsIndices arrays
 */
export function createDefaultIndices(rowCount: number, columnCount: number) {
  return {
    rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
    columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
  };
}
