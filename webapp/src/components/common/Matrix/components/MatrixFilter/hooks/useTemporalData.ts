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
import { getHourOfYear, getWeekFromDayOfYear } from "@/utils/date/dateUtils";
import type { DateTimes, TimeFrequencyType } from "../../../shared/types";
import { TIME_INDEXING } from "../constants";
import { getDefaultRangeForIndexType } from "../utils/dateUtils";
import { getDayOfYear } from "date-fns";
interface UseTemporalDataProps {
  dateTime?: DateTimes;
  isTimeSeries: boolean;
  timeFrequency?: TimeFrequencyType;
}

interface ParsedDateInfo {
  date: Date | null;
  dayOfYear: number | null;
  hourOfYear: number | null;
  dayOfMonth: number | null;
  week: number | null;
  month: number | null;
  dayHour: number | null;
  weekday: number | null;
}

export function useTemporalData({ dateTime, isTimeSeries }: UseTemporalDataProps) {
  const indexTypeRanges = useMemo(() => {
    return Object.values(TIME_INDEXING).reduce(
      (acc, type) => {
        acc[type] = getDefaultRangeForIndexType(type);
        return acc;
      },
      {} as Record<string, { min: number; max: number }>,
    );
  }, []);

  const parsedDates = useMemo(() => {
    if (!dateTime || !isTimeSeries || dateTime.values.length === 0) {
      return [];
    }

    return dateTime.values.map((date): ParsedDateInfo => {
      try {
        const dayOfYear = getDayOfYear(date);
        return {
          date,
          dayOfYear: dayOfYear,
          hourOfYear: getHourOfYear(date),
          dayOfMonth: date.getDate(),
          week: getWeekFromDayOfYear(dayOfYear), //TODO: should be consistent with formatting ?
          month: date.getMonth() + 1,
          dayHour: date.getHours(),
          weekday: date.getDay() + 1,
        };
      } catch {
        return {
          date: null,
          dayOfYear: null,
          hourOfYear: null,
          dayOfMonth: null,
          week: null,
          month: null,
          dayHour: null,
          weekday: null,
        };
      }
    });
  }, [dateTime, isTimeSeries]);

  const valuesByIndexType = useMemo(() => {
    // Start with a fresh object using the default ranges
    const result = { ...indexTypeRanges } as Record<
      string,
      { min: number; max: number; uniqueValues?: number[] }
    >;

    // Set static values that don't depend on data
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

    // Only try to extract data-based values if we have parsed dates
    if (parsedDates.length > 0) {
      // Define mapping from indexing type to parsed data property
      const indexTypeToProperty: Record<string, keyof ParsedDateInfo> = {
        [TIME_INDEXING.DAY_OF_YEAR]: "dayOfYear",
        [TIME_INDEXING.HOUR_YEAR]: "hourOfYear",
        [TIME_INDEXING.DAY_OF_MONTH]: "dayOfMonth",
        [TIME_INDEXING.WEEK]: "week",
      };

      // Only update the ranges that should be data-dependent
      const dynamicTypes = [
        TIME_INDEXING.DAY_OF_YEAR,
        TIME_INDEXING.HOUR_YEAR,
        TIME_INDEXING.DAY_OF_MONTH,
        TIME_INDEXING.WEEK,
      ];

      for (const indexType of dynamicTypes) {
        const property = indexTypeToProperty[indexType];

        if (!property) {
          continue;
        }

        const values = parsedDates
          .map((parsed) => parsed[property] as number | null)
          .filter((value): value is number => value !== null);

        if (values.length > 0) {
          const uniqueSet = new Set(values);
          const uniqueValues = Array.from(uniqueSet).sort((a, b) => a - b);
          result[indexType] = {
            min: Math.min(...uniqueValues),
            max: Math.max(...uniqueValues),
            uniqueValues,
          };
        }
      }
    }

    return result;
  }, [parsedDates, indexTypeRanges]);

  const temporalValues = useMemo(() => {
    if (parsedDates.length === 0) {
      return {};
    }

    const result: Record<string, number[]> = {};

    // Define mapping from indexing type to parsed data property
    const indexTypeToProperty: Record<string, keyof ParsedDateInfo> = {
      [TIME_INDEXING.DAY_OF_YEAR]: "dayOfYear",
      [TIME_INDEXING.HOUR_YEAR]: "hourOfYear",
      [TIME_INDEXING.DAY_OF_MONTH]: "dayOfMonth",
      [TIME_INDEXING.WEEK]: "week",
      [TIME_INDEXING.MONTH]: "month",
      [TIME_INDEXING.DAY_HOUR]: "dayHour",
      [TIME_INDEXING.WEEKDAY]: "weekday",
    };

    for (const indexType of Object.values(TIME_INDEXING)) {
      const property = indexTypeToProperty[indexType];

      if (!property) {
        continue;
      }

      result[indexType] = parsedDates
        .map((parsed) => parsed[property] as number | null)
        .filter((value): value is number => value !== null);
    }

    return result;
  }, [parsedDates]);

  return {
    indexTypeRanges,
    valuesByIndexType,
    temporalValues,
  };
}
