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
import { FILTER_TYPES } from "../constants";
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
    } else if (filter.columnsFilter.type === FILTER_TYPES.LIST && filter.columnsFilter.list) {
      columnsIndices = filter.columnsFilter.list
        .map((idx) => idx - 1)
        .filter((idx) => idx >= 0 && idx < columnCount);
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
