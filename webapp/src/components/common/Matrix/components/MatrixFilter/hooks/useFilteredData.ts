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
import type { FilterState, FilterCriteria } from "../types";
import type { TimeFrequencyType } from "../../../shared/types";
import { FILTER_TYPES, FILTER_OPERATORS } from "../constants";
import { processRowFilters } from "../utils";

interface UseFilteredDataProps {
  filter: FilterState;
  dateTime?: string[];
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
  rowCount: number;
  columnCount: number;
}

export function useFilteredData({
  filter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  rowCount,
  columnCount,
}: UseFilteredDataProps): FilterCriteria {
  return useMemo((): FilterCriteria => {
    if (!filter.active) {
      // Return all rows and columns when filter is not active
      return {
        columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
        rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
      };
    }

    // Filter columns
    let columnsIndices: number[] = [];

    if (filter.columnsFilter.type === FILTER_TYPES.RANGE && filter.columnsFilter.range) {
      const { min, max } = filter.columnsFilter.range;

      columnsIndices = Array.from({ length: columnCount }, (_, i) => i + 1)
        .filter((idx) => idx >= min && idx <= max)
        .map((idx) => idx - 1); // Convert to 0-based index
    } else if (filter.columnsFilter.type === FILTER_TYPES.LIST) {
      const operator = filter.columnsFilter.operator || FILTER_OPERATORS.EQUALS;
      const list = filter.columnsFilter.list || [];

      if (list.length === 0) {
        columnsIndices = [];
      } else {
        const allIndices = Array.from({ length: columnCount }, (_, i) => i + 1);

        switch (operator) {
          case FILTER_OPERATORS.EQUALS:
            columnsIndices = list
              .map((idx) => idx - 1)
              .filter((idx) => idx >= 0 && idx < columnCount);
            break;
          case FILTER_OPERATORS.GREATER_THAN: {
            const gtThreshold = Math.min(...list);
            columnsIndices = allIndices.filter((idx) => idx > gtThreshold).map((idx) => idx - 1);
            break;
          }
          case FILTER_OPERATORS.LESS_THAN: {
            const ltThreshold = Math.max(...list);
            columnsIndices = allIndices.filter((idx) => idx < ltThreshold).map((idx) => idx - 1);
            break;
          }
          case FILTER_OPERATORS.GREATER_EQUAL: {
            const gteThreshold = Math.min(...list);
            columnsIndices = allIndices.filter((idx) => idx >= gteThreshold).map((idx) => idx - 1);
            break;
          }
          case FILTER_OPERATORS.LESS_EQUAL: {
            const lteThreshold = Math.max(...list);
            columnsIndices = allIndices.filter((idx) => idx <= lteThreshold).map((idx) => idx - 1);
            break;
          }
          case FILTER_OPERATORS.RANGE:
            // For range operator, treat the list as individual values to include
            columnsIndices = list
              .map((idx) => idx - 1)
              .filter((idx) => idx >= 0 && idx < columnCount);
            break;
          default:
            columnsIndices = list
              .map((idx) => idx - 1)
              .filter((idx) => idx >= 0 && idx < columnCount);
        }
      }
    }

    // Process multiple row filters and get combined indices
    const rowsIndices: number[] = processRowFilters(
      filter,
      dateTime,
      isTimeSeries,
      timeFrequency,
      rowCount,
    );

    return { columnsIndices, rowsIndices };
  }, [filter, dateTime, isTimeSeries, timeFrequency, rowCount, columnCount]);
}
