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

// Supported locales
export const SUPPORTED_LOCALES = ["en", "fr"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

// Weekday names in different languages
export const WEEKDAY_NAMES = {
  en: {
    long: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    short: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    abbreviation: ["sun", "mon", "tue", "wed", "thu", "fri", "sat"],
  },
  fr: {
    long: ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
    short: ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"],
    abbreviation: ["dim", "lun", "mar", "mer", "jeu", "ven", "sam"],
  },
} as const;

// Month names in different languages
export const MONTH_NAMES = {
  en: {
    long: [
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
    ],
    short: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    abbreviation: [
      "jan",
      "feb",
      "mar",
      "apr",
      "may",
      "jun",
      "jul",
      "aug",
      "sep",
      "oct",
      "nov",
      "dec",
    ],
  },
  fr: {
    long: [
      "Janvier",
      "Février",
      "Mars",
      "Avril",
      "Mai",
      "Juin",
      "Juillet",
      "Août",
      "Septembre",
      "Octobre",
      "Novembre",
      "Décembre",
    ],
    short: ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"],
    abbreviation: [
      "jan",
      "fév",
      "mar",
      "avr",
      "mai",
      "juin",
      "juil",
      "aoû",
      "sep",
      "oct",
      "nov",
      "déc",
    ],
  },
} as const;

// Weekday object for configuration (Monday-based, 1-7)
export const WeekDay = {
  Monday: "Monday",
  Tuesday: "Tuesday",
  Wednesday: "Wednesday",
  Thursday: "Thursday",
  Friday: "Friday",
  Saturday: "Saturday",
  Sunday: "Sunday",
} as const;

export type WeekDay = (typeof WeekDay)[keyof typeof WeekDay];

// Month object for configuration
export const Month = {
  January: "january",
  February: "february",
  March: "march",
  April: "april",
  May: "may",
  June: "june",
  July: "july",
  August: "august",
  September: "september",
  October: "october",
  November: "november",
  December: "december",
} as const;

export type Month = (typeof Month)[keyof typeof Month];

// Weekday index mapping (Monday = 1, Sunday = 7)
export const WEEKDAY_INDEX_MAP = {
  Monday: 1,
  Tuesday: 2,
  Wednesday: 3,
  Thursday: 4,
  Friday: 5,
  Saturday: 6,
  Sunday: 7,
} as const;

// Reverse mapping for weekday indices
export const INDEX_TO_WEEKDAY_MAP = {
  1: WeekDay.Monday,
  2: WeekDay.Tuesday,
  3: WeekDay.Wednesday,
  4: WeekDay.Thursday,
  5: WeekDay.Friday,
  6: WeekDay.Saturday,
  7: WeekDay.Sunday,
} as const;

// Month index mapping (1-based)
export const MONTH_INDEX_MAP = {
  january: 1,
  february: 2,
  march: 3,
  april: 4,
  may: 5,
  june: 6,
  july: 7,
  august: 8,
  september: 9,
  october: 10,
  november: 11,
  december: 12,
} as const;

// Reverse mapping for month indices
export const INDEX_TO_MONTH_MAP = {
  1: Month.January,
  2: Month.February,
  3: Month.March,
  4: Month.April,
  5: Month.May,
  6: Month.June,
  7: Month.July,
  8: Month.August,
  9: Month.September,
  10: Month.October,
  11: Month.November,
  12: Month.December,
} as const;

// Common date formats used in the application
export const DATE_FORMATS = {
  // ISO formats
  ISO_DATE_TIME: "yyyy-MM-dd HH:mm",
  ISO_DATE: "yyyy-MM-dd",

  // Matrix formats
  HOURLY_MATRIX: "EEE d MMM HH:mm", // e.g., "Mon 1 Jan 00:00"
  HOURLY_MATRIX_WITH_YEAR: "EEE d MMM yyyy HH:mm",
  DAILY_MATRIX: "EEE d MMM", // e.g., "Mon 1 Jan"

  // Simple formats
  TIME_ONLY: "HH:mm",
  DAY_MONTH: "d MMM",
  DAY_MONTH_TIME: "d MMM HH:mm",

  // Regional formats
  EUROPEAN_DATE: "dd/MM/yyyy",
  US_DATE: "MM/dd/yyyy",

  // Full formats
  FULL_MONTH: "MMMM d, yyyy",
  ABBREVIATED_MONTH: "MMM d, yyyy",
  EUROPEAN_ABBREVIATED: "d MMM yyyy",
  EUROPEAN_FULL: "d MMMM yyyy",
} as const;

// Time zone constants
export const TIME_ZONES = {
  UTC: "UTC",
  LOCAL: "local",
} as const;

// Days in different periods
export const DAYS_IN = {
  WEEK: 7,
  MONTH_MIN: 28,
  MONTH_MAX: 31,
  YEAR: 365,
  LEAP_YEAR: 366,
} as const;

// Hours in different periods
export const HOURS_IN = {
  DAY: 24,
  WEEK: 168,
  YEAR: 8760,
  LEAP_YEAR: 8784,
} as const;

// Week options for configuration
export const WEEK_OPTIONS = [
  { label: "MON - SUN", value: WeekDay.Monday },
  { label: "TUE - MON", value: WeekDay.Tuesday },
  { label: "WED - TUE", value: WeekDay.Wednesday },
  { label: "THU - WED", value: WeekDay.Thursday },
  { label: "FRI - THU", value: WeekDay.Friday },
  { label: "SAT - FRI", value: WeekDay.Saturday },
  { label: "SUN - SAT", value: WeekDay.Sunday },
];

// Year options for configuration
export const YEAR_OPTIONS = [
  { label: "JAN - DEC", value: Month.January },
  { label: "FEB - JAN", value: Month.February },
  { label: "MAR - FEB", value: Month.March },
  { label: "APR - MAR", value: Month.April },
  { label: "MAY - APR", value: Month.May },
  { label: "JUN - MAY", value: Month.June },
  { label: "JUL - JUN", value: Month.July },
  { label: "AUG - JUL", value: Month.August },
  { label: "SEP - AUG", value: Month.September },
  { label: "OCT - SEP", value: Month.October },
  { label: "NOV - OCT", value: Month.November },
  { label: "DEC - NOV", value: Month.December },
];

// Type helpers
export type WeekDayKey = keyof typeof WEEKDAY_INDEX_MAP;
export type MonthKey = keyof typeof MONTH_INDEX_MAP;
export type WeekDayIndex = (typeof WEEKDAY_INDEX_MAP)[WeekDayKey];
export type MonthIndex = (typeof MONTH_INDEX_MAP)[MonthKey];
