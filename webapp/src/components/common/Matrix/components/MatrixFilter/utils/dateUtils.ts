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
import { parseFlexibleDate as parseFlexibleDateBase } from "@/utils/date/dateUtils";
import {
  createLocalizedTemporalLabels,
  extractTemporalValue,
  getTemporalRange,
  type TimeIndexingType,
} from "@/utils/date/matrixDateUtils";
import { getCurrentLanguage } from "@/utils/i18nUtils";
import type { LocalizedTimeLabel, TemporalRange } from "../types";

/**
 * Attempts to parse a date string using multiple formats
 *
 * @param dateStr - The date string to parse
 * @returns A valid Date object or null if parsing failed
 */
export function parseFlexibleDate(dateStr: string): Date | null {
  const locale = getCurrentLanguage();
  return parseFlexibleDateBase(dateStr, locale);
}

/**
 * Extracts a numeric value from a date string based on the specified indexing type
 *
 * @param dateStr - The date string to process
 * @param indexingType - The type of temporal index to extract (day, month, etc.)
 * @returns A numeric value representing the requested temporal index
 * @throws Error if the date string cannot be parsed
 */
export function extractValueFromDate(dateStr: string, indexingType: TimeIndexingType): number {
  const locale = getCurrentLanguage();
  const date = parseFlexibleDate(dateStr);

  if (!date) {
    throw new Error(`Invalid date format: "${dateStr}"`);
  }

  return extractTemporalValue(dateStr, indexingType, locale);
}

/**
 * Gets the default min and max values for a given indexing type
 *
 * @param indexingType - The type of temporal index (day, month, etc.)
 * @returns An object with the min and max values
 */
export function getDefaultRangeForIndexType(indexingType: TimeIndexingType): TemporalRange {
  return getTemporalRange(indexingType);
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
): LocalizedTimeLabel[] {
  return createLocalizedTemporalLabels(type, t);
}
