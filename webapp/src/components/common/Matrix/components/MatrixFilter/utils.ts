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

import { FILTER_TYPES, TIME_INDEXING, TIME_FREQUENCY_INDEXING_MAP } from "./constants";
import type { FilterState, TemporalIndexingParams, TemporalOption, RowFilter } from "./types";
import { TimeFrequency } from "../../shared/constants";
import type { TimeFrequencyType } from "../../shared/types";

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

  // Extract temporal indices directly from date strings without parsing
  const timeIndices = dateTime.map((dateStr, index) => {
    // For many indexing types, we don't need to fully parse the date
    // We can extract the needed values directly from the date string patterns
    const { indexingType } = rowFilter;

    try {
      // Handle annual frequency differently
      if (timeFrequency === TimeFrequency.Annual) {
        // For annual data, we typically just use the index as is
        return { index, value: index + 1 };
      }

      // Time indexing based on string patterns - prevents parsing errors
      if (indexingType === TIME_INDEXING.MONTH) {
        // Look for month names in the string - simplistic approach
        const months = [
          "jan",
          "feb",
          "mar",
          "apr",
          "may",
          "jun",
          "jul",
          "aug",
          "sep",
          "oct",
          "nov",
          "dec",
          "jan",
          "fév",
          "mar",
          "avr",
          "mai",
          "juin",
          "juil",
          "aoû",
          "sep",
          "oct",
          "nov",
          "déc",
        ];

        for (let i = 0; i < months.length; i++) {
          if (dateStr.toLowerCase().includes(months[i])) {
            return { index, value: (i % 12) + 1 }; // 1-12
          }
        }
      } else if (indexingType === TIME_INDEXING.WEEKDAY) {
        // Look for day names in the string
        const days = [
          "mon",
          "tue",
          "wed",
          "thu",
          "fri",
          "sat",
          "sun",
          "lun",
          "mar",
          "mer",
          "jeu",
          "ven",
          "sam",
          "dim",
        ];

        for (let i = 0; i < days.length; i++) {
          if (dateStr.toLowerCase().includes(days[i])) {
            const dayValue = (i % 7) + 1; // 1-7 (Mon-Sun)
            return { index, value: dayValue };
          }
        }
      } else if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
        // Extract day number using regex - finds numbers 1-31
        const match = dateStr.match(/\b([1-9]|[12]\d|3[01])\b/);
        if (match) {
          return { index, value: Number.parseInt(match[0]) };
        }
      } else if (indexingType === TIME_INDEXING.DAY_HOUR) {
        // Extract hour using regex - finds times like 13:00
        const match = dateStr.match(/(\d{1,2})[:h]/);
        if (match) {
          return { index, value: Number.parseInt(match[1]) + 1 }; // Convert 0-23 to 1-24
        }
      } else if (indexingType === TIME_INDEXING.WEEK) {
        // Extract week number - finds "W. 01" pattern or numbers after "W"
        const match = dateStr.match(/[Ww]\.?\s*(\d{1,2})/);
        if (match) {
          return { index, value: Number.parseInt(match[1]) };
        }
      }

      // Fallback: use row index as the value
      return { index, value: index + 1 };
    } catch {
      // Silently handle date processing errors
      return { index, value: index + 1 };
    }
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
  } else if (rowFilter.type === FILTER_TYPES.LIST && rowFilter.list && rowFilter.list.length > 0) {
    matchingIndices = indices.filter(({ value }) => rowFilter.list?.includes(value));
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
 * @returns -
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
 * @returns Array of row indices that match ANY of the row filters
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
