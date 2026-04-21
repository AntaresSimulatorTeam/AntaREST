/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

/* eslint-disable vitest/no-conditional-expect */

import { Column, TIME_FREQUENCY_CONFIG, TimeFrequency } from "../constants";
import {
  calculateMatrixAggregates,
  formatGridNumber,
  generateCustomColumns,
  generateDateTime,
  generateTimeSeriesColumns,
  getAggregateTypes,
  parseClipboardNumber,
} from "../utils";
import {
  AGGREGATE_CONFIG_CASES,
  AGGREGATE_TEST_CASES,
  COLUMN_TEST_CASES,
  DATE_TIME_FORMAT_TEST_CASES,
  DATE_TIME_TEST_CASES,
  FORMAT_TEST_CASES,
} from "./fixtures";

describe("Matrix Utils", () => {
  beforeAll(() => {
    vi.mock("date-fns", async () => {
      const actual = (await vi.importActual("date-fns")) as typeof import("date-fns");

      return {
        ...actual,
        format: vi.fn((date: Date, formatString: string) => {
          if (formatString.includes("ww")) {
            const weekNumber = actual.getWeek(date);
            return `W. ${weekNumber.toString().padStart(2, "0")}`;
          }
          return actual.format(date, formatString);
        }),
      };
    });

    vi.useFakeTimers();
    vi.setSystemTime(new Date("2023-01-01T00:00:00.000Z"));
  });

  describe("DateTime Generation", () => {
    test.each(DATE_TIME_TEST_CASES)("generates correct $name", ({ config, expected }) => {
      const result = generateDateTime(config);
      expect(result).toEqual({
        values: expected,
        first_week_size: config.first_week_size,
        level: config.level,
      });
    });

    describe("Daylight Saving Time handling", () => {
      test("should generate consecutive hours without DST gaps or duplicates", () => {
        // Test with a date range that crosses DST transition in Europe
        const config = {
          start_date: "2023-03-26 00:00:00", // DST transition date in Europe
          steps: 24, // Full day
          first_week_size: 7,
          level: TimeFrequency.Hourly,
        };

        const result = generateDateTime(config);

        // Extract hours from the generated strings
        const hours = result.values.map((date) => {
          return date.getHours();
        });

        // Verify all hours are consecutive (starting from 00 of current day in UTC)
        expect(hours[0]).toBe(0); // Starts at 00:00 current day in UTC
        for (let i = 1; i < 24; i++) {
          expect(hours[i]).toBe(i);
        }
      });
    });
  });

  describe("Time Series Column Generation", () => {
    test.each(COLUMN_TEST_CASES)("handles $name correctly", ({ input, expectedLength }) => {
      const result = generateTimeSeriesColumns(input);
      expect(result).toHaveLength(expectedLength);

      if (expectedLength > 0) {
        if (input.startIndex) {
          expect(result[0].id).toBe(`data${input.startIndex}`);
          expect(result[0].title).toBe(`${input.prefix || "TS"} ${input.startIndex}`);
        } else {
          expect(result[0]).toEqual({
            id: "data1",
            title: "TS 1",
            type: Column.Number,
            style: "normal",
            editable: input.editable ?? true,
          });
        }
      }
    });
  });

  describe("Matrix Aggregates Calculation", () => {
    test.each(AGGREGATE_TEST_CASES)(
      "calculates $name correctly",
      ({ matrix, aggregates, expected }) => {
        const aggregatesTypes = getAggregateTypes(aggregates);
        const result = calculateMatrixAggregates({ matrix, types: aggregatesTypes });
        expect(result).toEqual(expected);
      },
    );
  });

  describe("Number Formatting", () => {
    describe.each(FORMAT_TEST_CASES)("$name", ({ cases }) => {
      test.each(cases)("$description", ({ value, maxDecimals, expected }) => {
        expect(formatGridNumber({ value, maxDecimals })).toBe(expected);
      });
    });
  });

  describe("parseClipboardNumber", () => {
    test.each([
      // International / SI (space thousands, period decimal)
      { input: "1 234 567.89", expected: 1234567.89 },
      { input: "1 234 567", expected: 1234567 },
      // US / UK (comma thousands, period decimal)
      { input: "1,234,567.89", expected: 1234567.89 },
      { input: "1,234,567", expected: 1234567 },
      { input: "1,234.56", expected: 1234.56 },
      // European (period thousands, comma decimal)
      { input: "1.234.567,89", expected: 1234567.89 },
      { input: "1.234.567", expected: 1234567 },
      { input: "1.234,56", expected: 1234.56 },
      // Plain numbers
      { input: "1234567.89", expected: 1234567.89 },
      { input: "1234567", expected: 1234567 },
      // Single comma: exactly 3 digits after → thousands separator (US/UK "4,567" = 4567)
      { input: "4,567", expected: 4567 },
      { input: "1,000", expected: 1000 },
      // Single comma: ≠ 3 digits after → decimal separator (European "1234,56" = 1234.56)
      { input: "1234,56", expected: 1234.56 },
      { input: "0,5", expected: 0.5 },
      { input: "12,1234", expected: 12.1234 },
      // Negative numbers
      { input: "-1,234,567.89", expected: -1234567.89 },
      { input: "-1.234.567,89", expected: -1234567.89 },
      { input: "-1234,56", expected: -1234.56 },
      // Small decimals
      { input: "0.5", expected: 0.5 },
      // Whitespace padding
      { input: "  1 234.5  ", expected: 1234.5 },
      // Invalid
      { input: "", expected: NaN },
      { input: "abc", expected: NaN },
    ])('parses "$input" → $expected', ({ input, expected }) => {
      const result = parseClipboardNumber(input);

      if (Number.isNaN(expected)) {
        expect(result).toBeNaN();
      } else {
        expect(result).toBe(expected);
      }
    });
  });

  describe("Custom Column Generation", () => {
    test("generates columns with correct properties", () => {
      const titles = ["Custom 1", "Custom 2", "Custom 3"];
      const width = 100;

      const result = generateCustomColumns({ titles, width });
      expect(result).toHaveLength(3);

      result.forEach((column, index) => {
        expect(column).toEqual({
          id: `custom${index + 1}`,
          title: titles[index],
          width: 100,
          type: Column.Number,
          editable: true,
        });
      });
    });
  });

  describe("Aggregate Type Configuration", () => {
    test.each(AGGREGATE_CONFIG_CASES)("handles $name correctly", ({ aggregates, expected }) => {
      expect(getAggregateTypes(aggregates)).toEqual(expected);
    });
  });
});

describe("DateTime formatting", () => {
  test.each(DATE_TIME_FORMAT_TEST_CASES)("format correct $name", ({ input, expected }) => {
    const result = input.values.map((date) =>
      TIME_FREQUENCY_CONFIG[input.level].format(date, input.first_week_size),
    );
    expect(result).toEqual(expected);
  });
});
