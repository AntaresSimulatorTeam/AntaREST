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

import { getDate, getDayOfYear, getHours, getMonth } from "date-fns";
import type { TFunction } from "i18next";
import { toError } from "../fnUtils";
import { DAYS_IN, HOURS_IN, MONTH_NAMES, type SupportedLocale, WEEKDAY_NAMES } from "./constants";
import {
  extractDayOfMonth,
  extractHour,
  findMonthIndex,
  findWeekdayIndex,
  getHourOfYear,
  getWeekdayIndex,
  getWeekFromDayOfYear,
  parseFlexibleDate,
} from "./dateUtils";

// Time indexing types from matrix constants
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
 * Extract a temporal value from a date string based on indexing type
 *
 * @param dateStr - The date string to process
 * @param indexingType - The type of temporal index to extract
 * @param locale - Locale for parsing
 * @returns A numeric value representing the requested temporal index
 */
export function extractTemporalValue(
  dateStr: string,
  indexingType: TimeIndexingType,
  locale: SupportedLocale = "en",
): number {
  try {
    // For weekday indexing, try direct string matching first
    if (indexingType === TIME_INDEXING.WEEKDAY) {
      const weekdayIndex = findWeekdayIndex(dateStr, locale);
      if (weekdayIndex !== null) {
        return weekdayIndex;
      }
    }

    // For month indexing, try direct string matching first
    if (indexingType === TIME_INDEXING.MONTH) {
      const monthIndex = findMonthIndex(dateStr, locale);
      if (monthIndex !== null) {
        return monthIndex;
      }
    }

    // Try to parse the full date
    const parsedDate = parseFlexibleDate(dateStr, locale);

    if (parsedDate) {
      switch (indexingType) {
        case TIME_INDEXING.MONTH:
          return getMonth(parsedDate) + 1; // getMonth is 0-based

        case TIME_INDEXING.WEEKDAY:
          return getWeekdayIndex(parsedDate);

        case TIME_INDEXING.DAY_OF_MONTH:
          return getDate(parsedDate);

        case TIME_INDEXING.DAY_HOUR:
          return getHours(parsedDate); // Keep 0-23

        case TIME_INDEXING.WEEK: {
          const dayOfYear = getDayOfYear(parsedDate);
          return getWeekFromDayOfYear(dayOfYear);
        }

        case TIME_INDEXING.DAY_OF_YEAR:
          return getDayOfYear(parsedDate);

        case TIME_INDEXING.HOUR_YEAR:
          return getHourOfYear(parsedDate);

        default:
          throw new Error(`Unknown indexing type: ${indexingType}`);
      }
    }

    // Fallback to pattern matching for specific types
    if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
      const day = extractDayOfMonth(dateStr);
      if (day !== null) {
        return day;
      }
    }

    if (indexingType === TIME_INDEXING.DAY_HOUR) {
      const hour = extractHour(dateStr);
      if (hour !== null) {
        return hour; // Keep 0-23
      }
    }

    throw new Error(
      `Unable to extract temporal value from "${dateStr}" for indexing type: ${indexingType}`,
    );
  } catch (error) {
    throw new Error(
      `Failed to extract temporal value from "${dateStr}" for indexing type: ${indexingType}: ${toError(error)}`,
    );
  }
}

/**
 * Get the default range for a temporal indexing type
 *
 * @param indexingType - The type of temporal index
 * @returns Object with min and max values
 */
export function getTemporalRange(indexingType: TimeIndexingType): { min: number; max: number } {
  switch (indexingType) {
    case TIME_INDEXING.DAY_OF_MONTH:
      return { min: 1, max: DAYS_IN.MONTH_MAX };

    case TIME_INDEXING.MONTH:
      return { min: 1, max: 12 };

    case TIME_INDEXING.WEEKDAY:
      return { min: 1, max: DAYS_IN.WEEK };

    case TIME_INDEXING.DAY_HOUR:
      return { min: 0, max: 23 };

    case TIME_INDEXING.DAY_OF_YEAR:
      return { min: 1, max: DAYS_IN.LEAP_YEAR };

    case TIME_INDEXING.WEEK:
      return { min: 1, max: 53 };

    case TIME_INDEXING.HOUR_YEAR:
      return { min: 1, max: HOURS_IN.YEAR };

    default:
      return { min: 1, max: 100 };
  }
}

/**
 * Create localized temporal labels for UI components
 *
 * @param type - Either "month" or "weekday"
 * @param t - Translation function
 * @returns Array of label objects
 */
export function createLocalizedTemporalLabels(
  type: "month" | "weekday",
  t: TFunction,
): Array<{ value: number; label: string; shortLabel: string }> {
  if (type === "month") {
    const monthKeys = [
      "january",
      "february",
      "march",
      "april",
      "may",
      "june",
      "july",
      "august",
      "september",
      "october",
      "november",
      "december",
    ];

    return monthKeys.map((key, index) => ({
      value: index + 1,
      label: t(`date.${key}`),
      shortLabel: t(`date.short.${key}`),
    }));
  }

  // Weekday labels
  const weekdayKeys = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ];

  return weekdayKeys.map((key, index) => ({
    value: index + 1,
    label: t(`date.${key}`),
    shortLabel: t(`date.short.${key}`),
  }));
}

/**
 * Check if a temporal value is within the valid range
 *
 * @param value - The value to check
 * @param indexingType - The temporal indexing type
 * @returns True if valid
 */
export function isValidTemporalValue(value: number, indexingType: TimeIndexingType): boolean {
  const range = getTemporalRange(indexingType);
  return value >= range.min && value <= range.max;
}

/**
 * Format temporal value for display
 *
 * @param value - The temporal value
 * @param indexingType - The temporal indexing type
 * @param format - Long or short format
 * @param locale - Locale for formatting
 * @returns Formatted string
 */
export function formatTemporalValue(
  value: number,
  indexingType: TimeIndexingType,
  format: "long" | "short" = "short",
  locale: SupportedLocale = "en",
): string {
  if (!isValidTemporalValue(value, indexingType)) {
    return String(value);
  }

  switch (indexingType) {
    case TIME_INDEXING.MONTH:
      return MONTH_NAMES[locale][format][value - 1];

    case TIME_INDEXING.WEEKDAY: {
      // Convert Monday=1 to array index
      const arrayIndex = value === 7 ? 0 : value;
      return WEEKDAY_NAMES[locale][format][arrayIndex];
    }

    case TIME_INDEXING.DAY_HOUR:
      // Format hour value (0-23) as "00:00" to "23:00"
      // This provides standard 24-hour time notation for better UX
      // Examples: 0 -> "00:00", 12 -> "12:00", 23 -> "23:00"
      return `${String(value).padStart(2, "0")}:00`;

    case TIME_INDEXING.WEEK:
      return `Week ${value}`;

    default:
      return String(value);
  }
}
