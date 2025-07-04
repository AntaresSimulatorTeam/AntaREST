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

import { getDate, getDay, getDayOfYear, getHours, isValid, parse } from "date-fns";
import { enUS, fr } from "date-fns/locale";
import { DATE_FORMATS, MONTH_NAMES, type SupportedLocale, WEEKDAY_NAMES } from "./constants";

/**
 * Get the appropriate date-fns locale object
 *
 * @param locale - The locale to use
 * @returns The date-fns locale object
 */
export function getDateFnsLocale(locale: SupportedLocale = "en") {
  return locale === "fr" ? fr : enUS;
}

/**
 * Parse a flexible date string using multiple formats
 *
 * @param dateStr - The date string to parse
 * @param locale - The locale to use for parsing
 * @returns A valid Date object or null if parsing failed
 */
export function parseFlexibleDate(dateStr: string, locale: SupportedLocale = "en"): Date | null {
  const dateFnsLocale = getDateFnsLocale(locale);

  // Try each format until we find one that works
  const formats = Object.values(DATE_FORMATS);

  for (const formatStr of formats) {
    try {
      const parsedDate = parse(dateStr, formatStr, new Date(), { locale: dateFnsLocale });
      if (isValid(parsedDate)) {
        return parsedDate;
      }
    } catch {
      // Continue to next format
    }
  }

  // Special handling for formats without year
  if (!dateStr.includes("20")) {
    const currentYear = new Date().getFullYear();

    // Try common patterns and add current year
    const patternsWithYear = [
      // "Mon 1 Jan 00:00" -> "Mon 1 Jan 2024 00:00"
      dateStr.replace(/^(\w{3}\s+\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})$/, `$1 ${currentYear}$2`),
      // "1 Jan 00:00" -> "1 Jan 2024 00:00"
      dateStr.replace(/^(\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})$/, `$1 ${currentYear}$2`),
      // Generic pattern
      dateStr.replace(/(\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})?/, `$1 ${currentYear}$2`),
    ];

    for (const dateWithYear of patternsWithYear) {
      for (const formatStr of formats) {
        try {
          const parsedDate = parse(dateWithYear, formatStr, new Date(), { locale: dateFnsLocale });
          if (isValid(parsedDate)) {
            return parsedDate;
          }
        } catch {
          // Continue
        }
      }
    }
  }

  return null;
}

/**
 * Find weekday index from a string (Monday = 1, Sunday = 7)
 *
 * @param dateStr - The string to search in
 * @param locale - The locale to use
 * @returns Weekday index (1-7) or null if not found
 */
export function findWeekdayIndex(dateStr: string, locale: SupportedLocale = "en"): number | null {
  const lowerStr = dateStr.toLowerCase();
  const weekdayNames = WEEKDAY_NAMES[locale];

  // Check abbreviations first (more specific)
  for (let i = 0; i < weekdayNames.abbreviation.length; i++) {
    if (lowerStr.startsWith(weekdayNames.abbreviation[i])) {
      // Convert from 0-based Sunday=0 to 1-based Monday=1
      return i === 0 ? 7 : i;
    }
  }

  // Check short names
  for (let i = 0; i < weekdayNames.short.length; i++) {
    if (lowerStr.startsWith(weekdayNames.short[i].toLowerCase())) {
      return i === 0 ? 7 : i;
    }
  }

  return null;
}

/**
 * Find month index from a string (1-based)
 *
 * @param dateStr - The string to search in
 * @param locale - The locale to use
 * @returns Month index (1-12) or null if not found
 */
export function findMonthIndex(dateStr: string, locale: SupportedLocale = "en"): number | null {
  const lowerStr = dateStr.toLowerCase();
  const monthNames = MONTH_NAMES[locale];

  // Check abbreviations
  for (let i = 0; i < monthNames.abbreviation.length; i++) {
    if (lowerStr.includes(monthNames.abbreviation[i])) {
      return i + 1;
    }
  }

  // Check short names
  for (let i = 0; i < monthNames.short.length; i++) {
    if (lowerStr.includes(monthNames.short[i].toLowerCase())) {
      return i + 1;
    }
  }

  return null;
}

/**
 * Get weekday index from Date object (Monday = 1, Sunday = 7)
 *
 * @param date - The date object
 * @returns Weekday index (1-7)
 */
export function getWeekdayIndex(date: Date): number {
  const day = getDay(date);
  // Convert from Sunday=0 to Monday=1 format
  return day === 0 ? 7 : day;
}

/**
 * Extract day of month from a string
 *
 * @param dateStr - The string to extract from
 * @returns Day of month (1-31) or null
 */
export function extractDayOfMonth(dateStr: string): number | null {
  // Try parsing first
  const date = parseFlexibleDate(dateStr);
  if (date) {
    return getDate(date);
  }

  // Fallback to regex
  const match = dateStr.match(/\b([1-9]|[12]\d|3[01])\b/);
  return match ? Number.parseInt(match[0]) : null;
}

/**
 * Extract hour from a string
 *
 * @param dateStr - The string to extract from
 * @returns Hour (0-23) or null
 */
export function extractHour(dateStr: string): number | null {
  // Try parsing first
  const date = parseFlexibleDate(dateStr);
  if (date) {
    return getHours(date);
  }

  // Fallback to regex for time patterns
  const match = dateStr.match(/(\d{1,2})[:h]/);
  return match ? Number.parseInt(match[1]) : null;
}

/**
 * Get week number from day of year
 *
 * @param dayOfYear - Day of year (1-366)
 * @returns Week number (1-53)
 */
export function getWeekFromDayOfYear(dayOfYear: number): number {
  return Math.ceil(dayOfYear / 7);
}

/**
 * Get hour of year from date
 *
 * @param date - The date
 * @returns Hour of year (1-8760)
 */
export function getHourOfYear(date: Date): number {
  return (getDayOfYear(date) - 1) * 24 + getHours(date) + 1;
}
