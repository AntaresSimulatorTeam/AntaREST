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

import { TIME_INDEXING } from "@/components/Matrix/components/MatrixFilter/constants";
import type { TimeIndexingType } from "@/components/Matrix/components/MatrixFilter/types";
import {
  extractDateInfo,
  getTemporalValue,
} from "@/components/Matrix/components/MatrixFilter/utils";
import { getDefaultRangeForIndexType } from "@/components/Matrix/components/MatrixFilter/utils/dateUtils";
import { UTCDate } from "@date-fns/utc";
import { expect } from "vitest";

function extractValueFromDate(date: Date, indexing: TimeIndexingType): number {
  const dateInfo = extractDateInfo(date);
  return getTemporalValue(dateInfo, indexing);
}

describe("Hour Indexing", () => {
  describe("Hour of Year (HOUR_YEAR)", () => {
    test("should have a range of 1-8760", () => {
      const range = getDefaultRangeForIndexType(TIME_INDEXING.HOUR_YEAR);
      expect(range.min).toBe(1);
      expect(range.max).toBe(8760);
    });

    test("should extract hour 1 for midnight on January 1st", () => {
      const date = new UTCDate("2024-01-01T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(1);
    });

    test("should extract hour 24 for 11 PM on January 1st", () => {
      const date = new UTCDate("2024-01-01T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(24);
    });

    test("should extract hour 25 for midnight on January 2nd", () => {
      const date = new UTCDate("2024-01-02T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(25);
    });

    test("should extract hour 8784 for 11 PM on December 31st in a leap year", () => {
      // 2024 is a leap year (366 days * 24 hours = 8784 hours)
      const date = new UTCDate("2024-12-31T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(8784);
    });

    test("should extract hour 8760 for 11 PM on December 31st in a non-leap year", () => {
      // 2023 is not a leap year (365 days * 24 hours = 8760 hours)
      const date = new UTCDate("2023-12-31T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(8760);
    });
  });

  describe("Hour of Day (DAY_HOUR)", () => {
    test("should have a range of 0-23", () => {
      const range = getDefaultRangeForIndexType(TIME_INDEXING.DAY_HOUR);
      expect(range.min).toBe(0);
      expect(range.max).toBe(23);
    });

    test("should extract hour 0 for midnight (00:00)", () => {
      const date = new UTCDate("2024-01-15T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(0);
    });

    test("should extract hour 11 for 11:00 AM", () => {
      const date = new UTCDate("2024-01-15T11:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(11);
    });

    test("should extract hour 23 for 11 PM (23:00)", () => {
      const date = new UTCDate("2024-01-15T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(23);
    });
  });

  describe("Date info extraction", () => {
    test("Basic test", () => {
      const date = new UTCDate("2024-02-15T23:00:00Z");
      expect(extractDateInfo(date)).toEqual({
        dayHour: 23,
        dayOfMonth: 15,
        dayOfYear: 46,
        hourOfYear: 1104,
        month: 2,
        week: 7,
        weekday: 4, // Thursday, should be 4
      });
    });
  });

  describe("Temporal value extraction", () => {
    const dateInfo = {
      dayHour: 23,
      dayOfMonth: 15,
      dayOfYear: 46,
      hourOfYear: 1104,
      month: 2,
      week: 7,
      weekday: 4,
    };

    test("Hour of day extraction", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.DAY_HOUR)).toEqual(23);
    });
    test("Hour of year extraction", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.HOUR_YEAR)).toEqual(1104);
    });
    test("Day of month", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.DAY_OF_MONTH)).toEqual(15);
    });
    test("Day of year", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.DAY_OF_YEAR)).toEqual(46);
    });
    test("Mont extraction", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.MONTH)).toEqual(2);
    });
    test("Week extraction", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.WEEK)).toEqual(7);
    });
    test("Weekday extraction", () => {
      expect(getTemporalValue(dateInfo, TIME_INDEXING.WEEKDAY)).toEqual(4);
    });
  });
});
