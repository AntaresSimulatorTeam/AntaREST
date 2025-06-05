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

import { processRowFilters } from "../index";
import {
  FILTER_TYPES,
  TIME_INDEXING,
  FILTER_OPERATORS,
  type TimeIndexingType,
  type FilterType,
} from "../../constants";
import type { FilterState } from "../../types";

describe("Filter Combination Logic", () => {
  const createMockFilter = (
    rowsFilterLogic: "AND" | "OR" = "AND",
    filters: Array<{
      indexingType: TimeIndexingType;
      type: FilterType;
      list?: number[];
      range?: { min: number; max: number };
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
      operator: FILTER_OPERATORS.EQUALS,
    })),
    rowsFilterLogic,
    operation: {
      type: "Eq",
      value: 0,
    },
  });

  // Mock date/time data for a year (simplified - just marking months and weekdays)
  const mockDateTime = Array.from({ length: 365 }, (_, i) => {
    const date = new Date(Date.UTC(2024, 0, 1 + i)); // Start from Jan 1, 2024 UTC
    return date.toISOString();
  });

  describe("AND Logic (Intersection)", () => {
    it("should return only rows matching ALL filters", () => {
      const filter = createMockFilter("AND", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // January 2024 has 31 days, and contains 4 or 5 Mondays
      // We expect only the Mondays in January
      expect(result.length).toBeLessThanOrEqual(5);
      expect(result.length).toBeGreaterThanOrEqual(4);

      // Verify all results are actually Mondays in January
      for (const index of result) {
        const date = new Date(mockDateTime[index]);
        expect(date.getMonth()).toBe(0); // January is month 0
        expect(date.getDay()).toBe(1); // Monday is day 1
      }
    });

    it("should return empty array when filters have no intersection", () => {
      const filter = createMockFilter("AND", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);
      expect(result).toEqual([]);
    });

    it("should handle range filters with AND logic", () => {
      const filter = createMockFilter("AND", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // Verify all results are weekends in summer months
      for (const index of result) {
        const date = new Date(mockDateTime[index]);
        const month = date.getMonth() + 1; // getMonth() is 0-based
        const dayOfWeek = date.getDay();

        expect(month).toBeGreaterThanOrEqual(6);
        expect(month).toBeLessThanOrEqual(8);
        expect([0, 6]).toContain(dayOfWeek); // Sunday is 0, Saturday is 6
      }
    });
  });

  describe("OR Logic (Union)", () => {
    it("should return rows matching ANY filter", () => {
      const filter = createMockFilter("OR", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // Should include all January days + all Mondays in the year
      // January has 31 days, year has ~52 Mondays
      // Some Mondays are in January, so total should be less than 31 + 52
      expect(result.length).toBeGreaterThan(31); // At least all January days
      expect(result.length).toBeLessThan(83); // Less than sum due to overlap

      // Verify each result is either in January OR is a Monday
      for (const index of result) {
        const date = new Date(mockDateTime[index]);
        const isJanuary = date.getMonth() === 0;
        const isMonday = date.getDay() === 1;
        expect(isJanuary || isMonday).toBe(true);
      }
    });

    it("should handle multiple filters with no overlap", () => {
      const filter = createMockFilter("OR", [
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
      ]);

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // March has 31 days, September has 30 days = 61 total
      expect(result.length).toBe(61);
    });

    it("should remove duplicates when using OR logic", () => {
      const filter = createMockFilter("OR", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // Should have 12 results (one 1st day per month)
      expect(result.length).toBe(12);

      // Verify no duplicates
      const uniqueResults = [...new Set(result)];
      expect(uniqueResults.length).toBe(result.length);
    });
  });

  describe("Default Behavior", () => {
    it("should default to AND logic when rowsFilterLogic is not specified", () => {
      const filter: FilterState = {
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [1],
          operator: FILTER_OPERATORS.EQUALS,
        },
        rowsFilters: [
          {
            id: "filter-1",
            indexingType: TIME_INDEXING.MONTH,
            type: FILTER_TYPES.LIST,
            list: [1], // January
            operator: FILTER_OPERATORS.EQUALS,
          },
          {
            id: "filter-2",
            indexingType: TIME_INDEXING.WEEKDAY,
            type: FILTER_TYPES.LIST,
            list: [1], // Monday
            operator: FILTER_OPERATORS.EQUALS,
          },
        ],
        // rowsFilterLogic is not specified
        operation: {
          type: "Eq",
          value: 0,
        },
      };

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // Should behave like AND logic
      expect(result.length).toBeLessThanOrEqual(5); // Only Mondays in January
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty filter lists", () => {
      const filter = createMockFilter("AND", [
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [], // Empty list
        },
      ]);

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);
      expect(result).toEqual([]);
    });

    it("should handle single filter", () => {
      const filter = createMockFilter("AND", [
        {
          indexingType: TIME_INDEXING.MONTH,
          type: FILTER_TYPES.LIST,
          list: [7], // July
        },
      ]);

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);
      expect(result.length).toBe(31); // July has 31 days
    });

    it("should handle no filters", () => {
      const filter = createMockFilter("AND", []);
      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);
      expect(result.length).toBe(365); // All rows
    });

    it("should handle three or more filters with AND logic", () => {
      const filter = createMockFilter("AND", [
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

      const result = processRowFilters(filter, mockDateTime, true, undefined, 365);

      // Should only include Fridays in the first half of July
      for (const index of result) {
        const date = new Date(mockDateTime[index]);
        expect(date.getMonth()).toBe(6); // July is month 6
        expect(date.getDay()).toBe(5); // Friday
        expect(date.getDate()).toBeLessThanOrEqual(15);
      }
    });
  });
});
