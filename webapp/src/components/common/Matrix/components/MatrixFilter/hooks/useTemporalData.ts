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
import type { DateTimes, TimeFrequencyType } from "../../../shared/types";
import { TIME_INDEXING } from "../constants";
import { extractValueFromDate, getDefaultRangeForIndexType } from "../utils/dateUtils";

interface UseTemporalDataProps {
  dateTime?: DateTimes;
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
}

export function useTemporalData({ dateTime, isTimeSeries }: UseTemporalDataProps) {
  const indexTypeRanges = useMemo(() => {
    // Create a map of all default ranges
    return Object.values(TIME_INDEXING).reduce(
      (acc, type) => {
        acc[type] = getDefaultRangeForIndexType(type);
        return acc;
      },
      {} as Record<string, { min: number; max: number }>,
    );
  }, []);

  // Get the range values based on data or defaults
  const valuesByIndexType = useMemo(() => {
    // Start with a fresh object using the default ranges
    const result = { ...indexTypeRanges } as Record<
      string,
      { min: number; max: number; uniqueValues?: number[] }
    >;

    result[TIME_INDEXING.DAY_HOUR] = {
      min: 0,
      max: 23,
      uniqueValues: Array.from({ length: 24 }, (_, i) => i),
    };

    result[TIME_INDEXING.WEEKDAY] = {
      min: 1,
      max: 7,
      uniqueValues: Array.from({ length: 7 }, (_, i) => i + 1),
    };

    result[TIME_INDEXING.MONTH] = {
      min: 1,
      max: 12,
      uniqueValues: Array.from({ length: 12 }, (_, i) => i + 1),
    };

    // Only try to extract data-based values if we have time series data
    if (dateTime && isTimeSeries && dateTime.values.length > 0) {
      // Only update the ranges that should be data-dependent
      const dynamicTypes = [
        TIME_INDEXING.DAY_OF_YEAR,
        TIME_INDEXING.HOUR_YEAR,
        TIME_INDEXING.DAY_OF_MONTH,
        TIME_INDEXING.WEEK,
      ];

      for (const indexType of dynamicTypes) {
        try {
          const values = dateTime.values
            .map((date) => {
              try {
                return extractValueFromDate(date, indexType);
              } catch {
                return null;
              }
            })
            .filter((value): value is number => value !== null);

          if (values.length > 0) {
            const min = Math.min(...values);
            const max = Math.max(...values);
            const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
            result[indexType] = { min, max, uniqueValues };
          }
        } catch {
          // Keep defaults on error
        }
      }
    }

    return result;
  }, [dateTime, isTimeSeries, indexTypeRanges]);

  const temporalValues = useMemo(() => {
    if (!dateTime || !isTimeSeries || dateTime.values.length === 0) {
      return {};
    }

    const result: Record<string, number[]> = {};

    for (const indexType of Object.values(TIME_INDEXING)) {
      result[indexType] = dateTime.values
        .map((date) => {
          try {
            return extractValueFromDate(date, indexType);
          } catch {
            return null;
          }
        })
        .filter((value): value is number => value !== null);
    }

    return result;
  }, [dateTime, isTimeSeries]);

  return {
    indexTypeRanges,
    valuesByIndexType,
    temporalValues,
  };
}
