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

import {
  parseFlexibleDate as parseFlexibleDateBase,
  getCurrentLocale,
} from "@/utils/date/dateUtils";
import {
  extractTemporalValue,
  getTemporalRange,
  createLocalizedTemporalLabels,
  type TimeIndexingType,
} from "@/utils/date/matrixDateUtils";
import type { TFunction } from "i18next";

/**
 * Attempts to parse a date string using multiple formats
 *
 * @param dateStr - The date string to parse
 * @returns A valid Date object or null if parsing failed
 */
export function parseFlexibleDate(dateStr: string): Date | null {
  const locale = getCurrentLocale();
  return parseFlexibleDateBase(dateStr, locale);
}

/**
 * Extracts a numeric value from a date string based on the specified indexing type
 *
 * @param dateStr - The date string to process
 * @param indexingType - The type of temporal index to extract (day, month, etc.)
 * @param fallbackIndex - Fallback index to use if parsing fails
 * @returns A numeric value representing the requested temporal index
 */
export function extractValueFromDate(
  dateStr: string,
  indexingType: string,
  fallbackIndex: number,
): number {
  const locale = getCurrentLocale();
  return extractTemporalValue(dateStr, indexingType as TimeIndexingType, fallbackIndex, locale);
}

/**
 * Gets the default min and max values for a given indexing type
 *
 * @param indexingType - The type of temporal index (day, month, etc.)
 * @returns An object with the min and max values
 */
export function getDefaultRangeForIndexType(indexingType: string): { min: number; max: number } {
  return getTemporalRange(indexingType as TimeIndexingType);
}

/**
 * Creates localized arrays of months or weekdays for UI components
 *
 * @param type - Either "month" or "weekday"
 * @param t - The translation function from useTranslation()
 * @returns Array of objects with value, label, and shortLabel properties
 */
export function getLocalizedTimeLabels(
  type: "month" | "weekday",
  t: TFunction,
): Array<{ value: number; label: string; shortLabel: string }> {
  return createLocalizedTemporalLabels(type, t);
}
