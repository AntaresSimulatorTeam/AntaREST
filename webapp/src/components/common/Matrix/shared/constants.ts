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
  addDays,
  addHours,
  addMonths,
  addWeeks,
  addYears,
  type FirstWeekContainsDate,
  format,
  getWeek,
  startOfWeek,
} from "date-fns";
import { t } from "i18next";
import type { DateIncrementFunction, FormatFunction, TimeFrequencyType } from "./types";
import { getLocale } from "./utils";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export const Column = {
  DateTime: "datetime",
  Number: "number",
  Text: "text",
  Aggregate: "aggregate",
} as const;

export const Operation = {
  Add: "+",
  Sub: "-",
  Mul: "*",
  Div: "/",
  Abs: "ABS",
  Eq: "=",
} as const;

// !NOTE: Keep lowercase to match Glide Data Grid column ids
export const Aggregate = {
  Min: "min",
  Max: "max",
  Avg: "avg",
  Total: "total",
} as const;

export const TimeFrequency = {
  Annual: "annual",
  Monthly: "monthly",
  Weekly: "weekly",
  Daily: "daily",
  Hourly: "hourly",
} as const;

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

/**
 * Configuration object for different time frequencies
 *
 * This object defines how to increment and format dates for various time frequencies.
 * The WEEKLY frequency is of particular interest as it implements custom week starts
 * and handles ISO week numbering.
 */
export const TIME_FREQUENCY_CONFIG: Record<
  TimeFrequencyType,
  {
    increment: DateIncrementFunction;
    format: FormatFunction;
  }
> = {
  [TimeFrequency.Annual]: {
    increment: addYears,
    format: () => t("global.time.annual"),
  },
  [TimeFrequency.Monthly]: {
    increment: addMonths,
    format: (date: Date) => format(date, "MMM", { locale: getLocale() }),
  },
  [TimeFrequency.Weekly]: {
    increment: addWeeks,
    format: (date: Date, firstWeekSize: number) => {
      const weekStart = startOfWeek(date, { locale: getLocale() });

      const weekNumber = getWeek(weekStart, {
        locale: getLocale(),
        weekStartsOn: firstWeekSize === 1 ? 0 : 1,
        firstWeekContainsDate: firstWeekSize as FirstWeekContainsDate,
      });

      return `${t("global.time.weekShort")} ${weekNumber.toString().padStart(2, "0")}`;
    },
  },
  [TimeFrequency.Daily]: {
    increment: addDays,
    format: (date: Date) => format(date, "EEE d MMM", { locale: getLocale() }),
  },
  [TimeFrequency.Hourly]: {
    increment: addHours,
    format: (date: Date) => format(date, "EEE d MMM HH:mm", { locale: getLocale() }),
  },
};
