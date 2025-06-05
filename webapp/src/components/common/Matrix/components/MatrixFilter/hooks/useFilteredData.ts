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

import { useMemo } from "react";
import * as R from "ramda";
import type { FilterState, FilterCriteria } from "../types";
import type { TimeFrequencyType } from "../../../shared/types";
import { FILTER_OPERATORS, FILTER_TYPES, type FilterOperatorType } from "../constants";
import { processRowFilters } from "../utils";

interface UseFilteredDataProps {
  filter: FilterState;
  dateTime?: string[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  rowCount: number;
  columnCount: number;
}

/**
 * Applies operator logic to filter indices based on the specified operator and values
 *
 * @param indices - Array of indices to filter
 * @param operator - The filter operator to apply
 * @param values - Array of values to use for filtering
 * @returns Filtered array of indices
 */
function applyOperator(
  indices: number[],
  operator: FilterOperatorType,
  values: number[],
): number[] {
  if (R.isEmpty(values)) {
    return [];
  }

  const predicates: Record<FilterOperatorType, (index: number) => boolean> = {
    [FILTER_OPERATORS.EQUALS]: R.flip(R.includes)(values),
    [FILTER_OPERATORS.GREATER_THAN]: R.gt(R.__, Math.min(...values)),
    [FILTER_OPERATORS.LESS_THAN]: R.lt(R.__, Math.max(...values)),
    [FILTER_OPERATORS.GREATER_EQUAL]: R.gte(R.__, Math.min(...values)),
    [FILTER_OPERATORS.LESS_EQUAL]: R.lte(R.__, Math.max(...values)),
    [FILTER_OPERATORS.RANGE]:
      values.length >= 2
        ? R.both(R.gte(R.__, Math.min(...values)), R.lte(R.__, Math.max(...values)))
        : R.flip(R.includes)(values),
  };

  const predicate = predicates[operator] || predicates[FILTER_OPERATORS.EQUALS];
  return R.filter(predicate, indices);
}

/**
 * Filters column indices based on the column filter configuration
 *
 * @param columnFilter - The column filter configuration containing type, range, list, and operator
 * @param columnCount - The total number of columns in the dataset
 * @returns Array of filtered column indices (0-based)
 */
function filterColumns(columnFilter: FilterState["columnsFilter"], columnCount: number): number[] {
  if (columnFilter.type === FILTER_TYPES.RANGE && columnFilter.range) {
    const { min, max } = columnFilter.range;
    // Generate 0-based indices directly
    const rangeIndices = R.range(Math.max(0, min - 1), Math.min(columnCount, max));
    return rangeIndices;
  }

  if (columnFilter.type === FILTER_TYPES.LIST) {
    const operator = columnFilter.operator || FILTER_OPERATORS.EQUALS;
    const list = columnFilter.list || [];

    // Work with 1-based values for user-facing logic, but return 0-based indices
    const allIndices = R.range(1, columnCount + 1);
    const filteredIndices = applyOperator(allIndices, operator, list);

    // Convert to 0-based and validate bounds
    return R.pipe(
      R.map(R.dec), // Convert to 0-based
      R.filter(R.both(R.gte(R.__, 0), R.lt(R.__, columnCount))),
    )(filteredIndices);
  }

  return [];
}

/**
 * Creates a default filter criteria with all indices
 *
 * @param rowCount - The total number of rows
 * @param columnCount - The total number of columns
 * @returns Filter criteria with all row and column indices
 */
const createDefaultCriteria = R.memoizeWith(
  (rowCount: number, columnCount: number) => `${rowCount}-${columnCount}`,
  (rowCount: number, columnCount: number): FilterCriteria => ({
    columnsIndices: R.range(0, columnCount),
    rowsIndices: R.range(0, rowCount),
  }),
);

/**
 * Hook to compute filtered row and column indices based on filter configuration
 *
 * @param props - The configuration object for filtering
 * @param props.filter - The filter state containing active status and filter configurations
 * @param props.dateTime - Array of date/time strings for time-based filtering
 * @param props.isTimeSeries - Whether the data represents a time series
 * @param props.timeFrequency - The frequency of the time series data
 * @param props.rowCount - Total number of rows in the dataset
 * @param props.columnCount - Total number of columns in the dataset
 * @returns Filter criteria containing arrays of filtered row and column indices
 */
export function useFilteredData({
  filter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  rowCount,
  columnCount,
}: UseFilteredDataProps): FilterCriteria {
  return useMemo(() => {
    // Return all indices when filter is inactive
    if (!filter.active) {
      return createDefaultCriteria(rowCount, columnCount);
    }

    // Filter on columns
    const columnsIndices = filterColumns(filter.columnsFilter, columnCount);

    // Filter on rows
    const rowsIndices = processRowFilters(filter, dateTime, isTimeSeries, timeFrequency, rowCount);

    return { columnsIndices, rowsIndices };
  }, [filter, dateTime, isTimeSeries, timeFrequency, rowCount, columnCount]);
}
