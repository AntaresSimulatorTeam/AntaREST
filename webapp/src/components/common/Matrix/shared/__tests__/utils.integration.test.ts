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

import { describe, expect, test } from "vitest";
import { TimeFrequency } from "../constants";
import type { DateTimeMetadataDTO } from "../types";
import { generateDateTime } from "../utils";

/**
 * Integration tests for date/time generation.
 * These tests verify the actual behavior without mocks,
 * particularly around Daylight Saving Time transitions.
 */
describe("DateTime Generation - Integration Tests", () => {
  describe("UTC behavior verification", () => {
    test("should not skip hours during spring DST transition (Europe)", () => {
      const config: DateTimeMetadataDTO = {
        start_date: "2023-03-26T00:00:00.000Z", // Last Sunday of March - DST starts in Europe
        steps: 5,
        first_week_size: 7,
        level: TimeFrequency.Hourly,
      };

      const result = generateDateTime(config);

      // Extract hours
      const hours = result.values.map((date) => date.getHours());

      // In UTC, there should be no gap
      expect(hours).toEqual([0, 1, 2, 3, 4]);
    });

    test("should not duplicate hours during fall DST transition (Europe)", () => {
      const config: DateTimeMetadataDTO = {
        start_date: "2023-10-29T00:00:00.000Z", // Last Sunday of October - DST ends in Europe
        steps: 5,
        first_week_size: 7,
        level: TimeFrequency.Hourly,
      };

      const result = generateDateTime(config);

      // Extract hours
      const hours = result.values.map((date) => date.getHours());

      // In UTC, there should be no duplicate
      expect(hours).toEqual([0, 1, 2, 3, 4]);
    });

    test("should generate 24 consecutive hours across DST boundary", () => {
      const config: DateTimeMetadataDTO = {
        start_date: "2023-03-26T00:00:00.000Z", // DST transition date
        steps: 24,
        first_week_size: 7,
        level: TimeFrequency.Hourly,
      };

      const result = generateDateTime(config);

      // Extract hours
      const hours = result.values.map((date) => date.getHours());

      // Should have exactly 24 hours starting from 00 (current day in UTC)
      expect(hours.length).toBe(24);
      expect(hours[0]).toBe(0); // Starts at 00:00 current day in UTC
      for (let i = 1; i < 24; i++) {
        expect(hours[i]).toBe(i);
      }

      // No duplicates
      const uniqueHours = new Set(hours);
      expect(uniqueHours.size).toBe(24);
    });

    test("should maintain consistent intervals across multiple days with DST", () => {
      const config: DateTimeMetadataDTO = {
        start_date: "2023-03-25T00:00:00.000Z", // Day before DST transition
        steps: 72, // 3 days
        first_week_size: 7,
        level: TimeFrequency.Hourly,
      };

      const result = generateDateTime(config);

      // Check that we have exactly 72 unique timestamps
      const uniqueResults = new Set(result.values);
      expect(uniqueResults.size).toBe(72);

      // Extract date and hour parts
      const dateHours = result.values.map((date) => {
        return {
          day: date.getDate(),
          hour: date.getHours(),
        };
      });

      // Verify continuous progression
      for (let i = 1; i < dateHours.length; i++) {
        const prev = dateHours[i - 1];
        const curr = dateHours[i];

        if (prev.hour === 23) {
          // Next should be hour 0 of next day
          expect(curr.hour).toBe(0);
          expect(curr.day).toBe(prev.day + 1);
        } else {
          // Same day, next hour
          expect(curr.hour).toBe(prev.hour + 1);
          expect(curr.day).toBe(prev.day);
        }
      }
    });

    test("should handle DST transitions for US timezones", () => {
      const config: DateTimeMetadataDTO = {
        start_date: "2023-03-12T00:00:00.000Z", // Second Sunday of March - DST starts in US
        steps: 5,
        first_week_size: 7,
        level: TimeFrequency.Hourly,
      };

      const result = generateDateTime(config);

      // Should still show consecutive hours in UTC
      const hours = result.values.map((date) => date.getHours());

      expect(hours).toEqual([0, 1, 2, 3, 4]);
    });

    test("should handle different time frequencies across DST", () => {
      const baseConfig = {
        start_date: "2023-03-20T00:00:00.000Z", // Week containing DST transition
        first_week_size: 7,
      };

      // Test daily frequency
      const dailyConfig: DateTimeMetadataDTO = {
        ...baseConfig,
        steps: 14, // Two weeks
        level: TimeFrequency.Daily,
      };
      const dailyResult = generateDateTime(dailyConfig);
      expect(dailyResult.level).toBe(TimeFrequency.Daily);
      expect(dailyResult.values.length).toBe(14);
      expect(new Set(dailyResult.values).size).toBe(14); // All unique

      // Test weekly frequency
      const weeklyConfig: DateTimeMetadataDTO = {
        ...baseConfig,
        steps: 4, // Four weeks
        level: TimeFrequency.Weekly,
      };
      const weeklyResult = generateDateTime(weeklyConfig);
      expect(weeklyResult.level).toBe(TimeFrequency.Weekly);
      expect(weeklyResult.values.length).toBe(4);
      expect(new Set(weeklyResult.values).size).toBe(4); // All unique
    });
  });
});
