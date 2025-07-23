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
import { DAYS_IN, HOURS_IN } from "./constants";

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
