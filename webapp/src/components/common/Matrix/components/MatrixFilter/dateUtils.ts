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

import { parse, getDate, getMonth, getDay, getHours, getDayOfYear, isValid } from "date-fns";
import { TIME_INDEXING } from "./constants";

// Common date formats to try when parsing strings
export const DATE_FORMATS = [
  "yyyy-MM-dd HH:mm", // ISO format with time
  "yyyy-MM-dd", // ISO format date only
  "EEE d MMM HH:mm", // Hourly matrix format (e.g., "Mon 1 Jan 00:00")
  "EEE d MMM yyyy HH:mm", // Hourly matrix format with year
  "d MMM HH:mm", // Without day name
  "dd/MM/yyyy", // European format
  "MM/dd/yyyy", // US format
  "MMMM d, yyyy", // Full month name
  "MMM d, yyyy", // Abbreviated month name
  "d MMM yyyy", // European with abbreviated month
  "d MMMM yyyy", // European with full month
  "EEE d MMM", // Day format without time
  "d MMM", // Simplified day month format
];

// Month abbreviations in different languages for pattern matching fallback
export const MONTH_ABBREVIATIONS = {
  en: ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
  fr: ["jan", "fév", "mar", "avr", "mai", "juin", "juil", "aoû", "sep", "oct", "nov", "déc"],
};

// Day abbreviations in different languages for pattern matching fallback
export const DAY_ABBREVIATIONS = {
  en: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
  fr: ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"],
};

/**
 * Attempts to parse a date string using multiple formats
 *
 * @param dateStr - The date string to parse
 * @returns A valid Date object or null if parsing failed
 */
export function parseFlexibleDate(dateStr: string): Date | null {
  // Try each format until we find one that works
  for (const format of DATE_FORMATS) {
    const parsedDate = parse(dateStr, format, new Date());

    if (isValid(parsedDate)) {
      return parsedDate;
    }
  }

  // Special handling for formats that might not have a year
  // For hourly matrix data that might be formatted without year
  if (!dateStr.includes("20")) {
    // Try adding current year to date strings without year
    const currentYear = new Date().getFullYear();

    // Handle different patterns for adding year
    let dateWithYear = dateStr;

    // Pattern 1: "Mon 1 Jan 00:00" -> "Mon 1 Jan 2024 00:00"
    if (/^\w{3}\s+\d{1,2}\s+\w{3}\s+\d{2}:\d{2}$/.test(dateStr)) {
      dateWithYear = dateStr.replace(
        /^(\w{3}\s+\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})$/,
        `$1 ${currentYear}$2`,
      );
    }
    // Pattern 2: "1 Jan 00:00" -> "1 Jan 2024 00:00"
    else if (/^\d{1,2}\s+\w{3}\s+\d{2}:\d{2}$/.test(dateStr)) {
      dateWithYear = dateStr.replace(/^(\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})$/, `$1 ${currentYear}$2`);
    }
    // Pattern 3: Generic pattern
    else {
      dateWithYear = dateStr.replace(/(\d{1,2}\s+\w{3})(\s+\d{2}:\d{2})?/, `$1 ${currentYear}$2`);
    }

    for (const format of DATE_FORMATS) {
      const parsedDate = parse(dateWithYear, format, new Date());

      if (isValid(parsedDate)) {
        return parsedDate;
      }
    }
  }

  return null;
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
  try {
    // First try to parse the date using standard formats
    const parsedDate = parseFlexibleDate(dateStr);

    if (parsedDate) {
      // Extract the appropriate value based on indexing type
      switch (indexingType) {
        case TIME_INDEXING.MONTH:
          return getMonth(parsedDate) + 1; // getMonth is 0-based, we want 1-12
        case TIME_INDEXING.WEEKDAY: {
          const day = getDay(parsedDate);
          // Convert from Sunday=0 to Monday=1 format
          return day === 0 ? 7 : day;
        }
        case TIME_INDEXING.DAY_OF_MONTH:
          return getDate(parsedDate);
        case TIME_INDEXING.DAY_HOUR:
          return getHours(parsedDate) + 1; // We want 1-24 instead of 0-23
        case TIME_INDEXING.WEEK: {
          const dayOfYear = getDayOfYear(parsedDate);
          return Math.ceil(dayOfYear / 7);
        }
        case TIME_INDEXING.DAY_OF_YEAR:
          return getDayOfYear(parsedDate);
        case TIME_INDEXING.HOUR_YEAR:
          return (getDayOfYear(parsedDate) - 1) * 24 + getHours(parsedDate) + 1;
        default:
          return fallbackIndex + 1;
      }
    }

    // If date parsing failed, fall back to pattern matching
    const lowerDateStr = dateStr.toLowerCase();

    if (indexingType === TIME_INDEXING.MONTH) {
      // Try to match month abbreviations
      for (const lang of Object.keys(MONTH_ABBREVIATIONS)) {
        const abbrs = MONTH_ABBREVIATIONS[lang as keyof typeof MONTH_ABBREVIATIONS];

        for (let i = 0; i < abbrs.length; i++) {
          if (lowerDateStr.includes(abbrs[i])) {
            return i + 1; // Month values are 1-12
          }
        }
      }
    } else if (indexingType === TIME_INDEXING.WEEKDAY) {
      // Try to match day abbreviations
      for (const lang of Object.keys(DAY_ABBREVIATIONS)) {
        const abbrs = DAY_ABBREVIATIONS[lang as keyof typeof DAY_ABBREVIATIONS];

        for (let i = 0; i < abbrs.length; i++) {
          if (lowerDateStr.includes(abbrs[i])) {
            return i + 1; // Day values are 1-7 (Mon-Sun)
          }
        }
      }
    } else if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
      // Extract day number using regex - finds numbers 1-31
      const match = dateStr.match(/\b([1-9]|[12]\d|3[01])\b/);

      if (match) {
        return Number.parseInt(match[0]);
      }
    } else if (indexingType === TIME_INDEXING.DAY_HOUR) {
      // Extract hour using regex - finds times like 13:00 or 13h
      const match = dateStr.match(/(\d{1,2})[:h]/);

      if (match) {
        return Number.parseInt(match[1]) + 1; // Convert 0-23 to 1-24
      }
    }

    // Fallback logic when date parsing fails
    // For week indexing on hourly data, calculate week from hour index
    if (indexingType === TIME_INDEXING.WEEK && fallbackIndex < 8760) {
      // Assuming fallbackIndex is hour of year (0-8759)
      // Calculate which week this hour belongs to
      // Simple calculation: Week 1 starts on January 1st
      const dayOfYear = Math.floor(fallbackIndex / 24) + 1; // 1-365
      const weekNumber = Math.ceil(dayOfYear / 7);
      return Math.min(weekNumber, 53); // Cap at 53 weeks
    }

    // Default fallback - use the index
    return fallbackIndex + 1;
  } catch {
    // If anything goes wrong, return the index
    return fallbackIndex + 1;
  }
}

/**
 * Gets the default min and max values for a given indexing type
 *
 * @param indexingType - The type of temporal index (day, month, etc.)
 * @returns An object with the min and max values
 */
export function getDefaultRangeForIndexType(indexingType: string): { min: number; max: number } {
  switch (indexingType) {
    case TIME_INDEXING.DAY_OF_MONTH:
      return { min: 1, max: 31 };
    case TIME_INDEXING.MONTH:
      return { min: 1, max: 12 };
    case TIME_INDEXING.WEEKDAY:
      return { min: 1, max: 7 };
    case TIME_INDEXING.DAY_HOUR:
      return { min: 1, max: 24 };
    case TIME_INDEXING.DAY_OF_YEAR:
      return { min: 1, max: 366 };
    case TIME_INDEXING.WEEK:
      return { min: 1, max: 53 };
    case TIME_INDEXING.HOUR_YEAR:
      return { min: 1, max: 8760 }; // 365 days * 24 hours
    default:
      return { min: 1, max: 100 };
  }
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
  t: (key: string) => string,
): Array<{ value: number; label: string; shortLabel: string }> {
  if (type === "month") {
    const monthNames = [
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

    const monthCaps = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];

    return Array.from({ length: 12 }, (_, i) => ({
      value: i + 1,
      label: t(`date.${monthNames[i]}`),
      shortLabel: t(`date.short${monthCaps[i]}`),
    }));
  }

  const dayNames = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const dayCaps = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  return Array.from({ length: 7 }, (_, i) => ({
    value: i + 1,
    label: t(`date.${dayNames[i]}`),
    shortLabel: t(`date.short${dayCaps[i]}`),
  }));
}
