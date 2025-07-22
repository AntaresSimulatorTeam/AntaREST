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

import { formatTemporalValue } from "@/utils/date/matrixDateUtils";
import { TIME_INDEXING } from "../constants";
import { extractValueFromDate, getDefaultRangeForIndexType } from "../utils/dateUtils";
import { UTCDate } from "@date-fns/utc";

describe("Hour Indexing", () => {
  describe("Hour of Year (HOUR_YEAR)", () => {
    it("should have a range of 1-8760", () => {
      const range = getDefaultRangeForIndexType(TIME_INDEXING.HOUR_YEAR);
      expect(range.min).toBe(1);
      expect(range.max).toBe(8760);
    });

    it("should extract hour 1 for midnight on January 1st", () => {
      const date = new UTCDate("2024-01-01T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(1);
    });

    it("should extract hour 24 for 11 PM on January 1st", () => {
      const date = new UTCDate("2024-01-01T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(24);
    });

    it("should extract hour 25 for midnight on January 2nd", () => {
      const date = new UTCDate("2024-01-02T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(25);
    });

    it("should extract hour 8784 for 11 PM on December 31st in a leap year", () => {
      // 2024 is a leap year (366 days * 24 hours = 8784 hours)
      const date = new UTCDate("2024-12-31T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(8784);
    });

    it("should extract hour 8760 for 11 PM on December 31st in a non-leap year", () => {
      // 2023 is not a leap year (365 days * 24 hours = 8760 hours)
      const date = new UTCDate("2023-12-31T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.HOUR_YEAR);
      expect(hour).toBe(8760);
    });
  });

  describe("Hour of Day (DAY_HOUR)", () => {
    it("should have a range of 0-23", () => {
      const range = getDefaultRangeForIndexType(TIME_INDEXING.DAY_HOUR);
      expect(range.min).toBe(0);
      expect(range.max).toBe(23);
    });

    it("should extract hour 0 for midnight (00:00)", () => {
      const date = new UTCDate("2024-01-15T00:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(0);
    });

    it("should extract hour 11 for 11:00 AM", () => {
      const date = new UTCDate("2024-01-15T11:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(11);
    });

    it("should extract hour 23 for 11 PM (23:00)", () => {
      const date = new UTCDate("2024-01-15T23:00:00Z");
      const hour = extractValueFromDate(date, TIME_INDEXING.DAY_HOUR);
      expect(hour).toBe(23);
    });

    it("should format hour 0 as '00:00'", () => {
      const formatted = formatTemporalValue(0, TIME_INDEXING.DAY_HOUR);
      expect(formatted).toBe("00:00");
    });

    it("should format hour 12 as '12:00'", () => {
      const formatted = formatTemporalValue(12, TIME_INDEXING.DAY_HOUR);
      expect(formatted).toBe("12:00");
    });

    it("should format hour 23 as '23:00'", () => {
      const formatted = formatTemporalValue(23, TIME_INDEXING.DAY_HOUR);
      expect(formatted).toBe("23:00");
    });
  });
});
