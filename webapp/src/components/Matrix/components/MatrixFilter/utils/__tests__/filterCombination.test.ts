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

import { FILTER_OPERATORS, FILTER_TYPES, TIME_INDEXING } from "../../constants";
import type { FilterOperatorType, FilterState, FilterType, TimeIndexingType } from "../../types";
import { extractDatesInfo, processRowFilters } from "../index";
import { UTCDate } from "@date-fns/utc";

describe("Filter Combination Logic", () => {
  const createMockFilter = (
    filters: Array<{
      indexingType: TimeIndexingType;
      type: FilterType;
      list?: number[];
      range?: { min: number; max: number };
      operator?: FilterOperatorType;
    }> = [],
  ): FilterState => ({
    active: true,
    columnsFilter: {
      type: FILTER_TYPES.LIST,
      list: [1],
      operator: FILTER_OPERATORS.EQUALS,
    },
    rowsFilters: filters.map((f, index) => ({
      id: `filter-${index}`,
      indexingType: f.indexingType,
      type: f.type,
      list: f.list,
      range: f.range,
      operator: f.operator || FILTER_OPERATORS.EQUALS,
    })),
    operation: {
      type: "Eq",
      value: 0,
    },
  });

  // Mock date/time data for a year (simplified - just marking months and weekdays)
  const mockValues = Array.from({ length: 365 }, (_, i) => {
    return new UTCDate(Date.UTC(2024, 0, 1 + i)); // Start from Jan 1, 2024 UTC
  });

  const mockDatesInfo = extractDatesInfo(mockValues);

  describe("Mixed Type Filters (AND between types, OR within types)", () => {
    it("should apply AND logic between different indexingTypes", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // January
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [1], // Monday
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // January 2024 has 31 days, and contains 4 or 5 Mondays
      // We expect only the Mondays in January
      expect(result.length).toBeLessThanOrEqual(5);
      expect(result.length).toBeGreaterThanOrEqual(4);

      // Verify all results are actually Mondays in January
      for (const index of result) {
        const date = new Date(mockValues[index]);
        expect(date.getMonth()).toBe(0); // January is month 0
        expect(date.getDay()).toBe(1); // Monday is day 1
      }
    });

    it("should return empty array when filters have no intersection", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [2], // February
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [31], // 31st day (February doesn't have 31 days)
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result).toEqual([]);
    });

    it("should handle range filters with AND logic between types", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.RANGE,
          range: { min: 6, max: 8 }, // June to August (summer)
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [6, 7], // Weekend (Saturday and Sunday)
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Verify all results are weekends in summer months
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth() + 1; // getMonth() is 0-based
        const dayOfWeek = date.getDay();

        expect(month).toBeGreaterThanOrEqual(6);
        expect(month).toBeLessThanOrEqual(8);
        expect([0, 6]).toContain(dayOfWeek); // Sunday is 0, Saturday is 6
      }
    });

    it("should apply OR logic within same indexingType", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // January
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [3], // March
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should include all days in January OR March
      expect(result.length).toBe(62); // January (31) + March (31) = 62 days

      // Verify each result is either in January or March
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth();
        expect([0, 2]).toContain(month); // January is 0, March is 2
      }
    });

    it("should apply OR within type and AND between types", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // January
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [3], // March
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [1], // Monday
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should include only Mondays in January OR March
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth();
        const dayOfWeek = date.getDay();

        expect(dayOfWeek).toBe(1); // Must be Monday
        expect([0, 2]).toContain(month); // Must be January or March
      }
    });

    it("should handle multiple filters of different types correctly", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [3], // March
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [9], // September
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [6, 7], // Weekend
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should include only weekends in March OR September
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth();
        const dayOfWeek = date.getDay();

        expect([0, 6]).toContain(dayOfWeek); // Must be Saturday or Sunday
        expect([2, 8]).toContain(month); // Must be March or September
      }
    });
  });

  describe("Same Type Duplicates", () => {
    it("should not duplicate results when same filter is applied multiple times", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // 1st of each month
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // Same filter - should not duplicate results
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should have 12 results (one 1st day per month)
      expect(result.length).toBe(12);

      // Verify no duplicates
      const uniqueResults = [...new Set(result)];
      expect(uniqueResults.length).toBe(result.length);
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty filter lists as no filter (show all rows)", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [], // Empty list
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result.length).toBe(365); // Should show all rows when list is empty
    });

    it("should treat empty list filters as no filter applied", () => {
      // Test with multiple empty list filters
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [], // Empty weekday filter
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [], // Empty month filter
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result.length).toBe(365); // All rows should be shown

      // Test mixing empty and non-empty filters
      const mixedFilter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [6], // Only June
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [], // Empty weekday filter (should not restrict)
        },
      ]);

      const mixedResult = processRowFilters(mixedFilter, mockDatesInfo, true, undefined, 365);
      expect(mixedResult.length).toBe(30); // Should show all days in June
    });

    it("should handle single filter", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [7], // July
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result.length).toBe(31); // July has 31 days
    });

    it("should handle no filters", () => {
      const filter = createMockFilter([]);
      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result.length).toBe(365); // All rows
    });

    it("should handle three or more filters correctly", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [7], // July
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [5], // Friday
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.RANGE,
          range: { min: 1, max: 15 }, // First half of month
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should only include Fridays in the first half of July
      for (const index of result) {
        const date = new Date(mockValues[index]);
        expect(date.getMonth()).toBe(6); // July is month 6
        expect(date.getDay()).toBe(5); // Friday
        expect(date.getDate()).toBeLessThanOrEqual(15);
      }
    });

    it("should handle complex scenario with multiple same-type filters", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [1], // January
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [3], // March
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [5], // May
        },
        {
          indexingType: TIME_INDEXING.WEEKDAY,
          type: FILTER_TYPES.LIST,
          list: [2, 4], // Tuesday and Thursday
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should include only Tuesdays and Thursdays in January, March, or May
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth();
        const dayOfWeek = date.getDay();

        expect([2, 4]).toContain(dayOfWeek); // Must be Tuesday or Thursday
        expect([0, 2, 4]).toContain(month); // Must be January, March, or May
      }
    });

    it("should handle mix of range and list filters of same type", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.RANGE,
          range: { min: 1, max: 5 }, // First 5 days
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [28, 29, 30, 31], // Last days
        },
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [6], // June
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // Should include days 1-5 OR 28-31 in June only
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const month = date.getMonth();
        const day = date.getDate();

        expect(month).toBe(5); // Must be June (month 5)
        const isFirstFiveDays = day >= 1 && day <= 5;
        const isLastDays = day >= 28 && day <= 31;
        expect(isFirstFiveDays || isLastDays).toBe(true);
      }
    });

    it("should handle filters with different operators correctly", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [15], // Using greater than operator (day > 15)
          operator: FILTER_OPERATORS.GREATER_THAN,
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [5], // Using less than operator (day < 5)
          operator: FILTER_OPERATORS.LESS_THAN,
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);

      // With OR logic within same type, should include days where (day > 15) OR (day < 5)
      // This includes days 1-4 and 16-31 of each month
      // January: 4 + 16 = 20 days, February: 4 + 13 = 17 days (28 days total)
      // Months with 30 days: 4 + 15 = 19 days each
      // Months with 31 days: 4 + 16 = 20 days each

      // Verify the results match the criteria
      for (const index of result) {
        const date = new Date(mockValues[index]);
        const dayOfMonth = date.getDate();
        const matchesGreaterThan = dayOfMonth > 15;
        const matchesLessThan = dayOfMonth < 5;
        expect(matchesGreaterThan || matchesLessThan).toBe(true);
      }

      // Rough calculation: ~19-20 days per month * 12 months = ~228-240 days
      expect(result.length).toBeGreaterThan(220);
      expect(result.length).toBeLessThan(250);
    });

    it("should return empty when no filter matches", () => {
      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [2], // February
        },
        {
          indexingType: TIME_INDEXING.DAY_OF_MONTH,
          type: FILTER_TYPES.LIST,
          list: [30, 31], // Days that don't exist in February
        },
      ]);

      const result = processRowFilters(filter, mockDatesInfo, true, undefined, 365);
      expect(result).toEqual([]);
    });

    it("should handle hour-based filters correctly", () => {
      // Create hourly mock data for a single day
      const hourlyValues = Array.from({ length: 24 }, (_, i) => {
        return new UTCDate(Date.UTC(2024, 0, 1, i, 0, 0));
      });

      const hourlyDatesInfo = extractDatesInfo(hourlyValues);

      const filter = createMockFilter([
        {
          indexingType: TIME_INDEXING.DAY_HOUR,
          type: FILTER_TYPES.LIST,
          list: [0, 1, 2], // Hours 0-2 (midnight to 2 AM)
        },
        {
          indexingType: TIME_INDEXING.DAY_HOUR,
          type: FILTER_TYPES.LIST,
          list: [22, 23], // Hours 22-23 (10 PM to 11 PM)
        },
      ]);

      const result = processRowFilters(filter, hourlyDatesInfo, true, undefined, 24);

      // Should include hours 0-2 OR 22-23 (5 total hours)
      const resultHours = result.map((index) => new Date(hourlyValues[index]).getUTCHours());
      const expectedHours = [0, 1, 2, 22, 23];

      // Check that we have the right number of results
      expect(result.length).toBe(5);

      // Check that all result hours are in our expected set
      for (const hour of resultHours) {
        expect(expectedHours).toContain(hour);
      }
    });
  });
});
