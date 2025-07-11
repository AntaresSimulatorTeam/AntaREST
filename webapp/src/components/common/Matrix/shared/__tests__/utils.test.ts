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

import { Column, TimeFrequency } from "../constants";
import {
  calculateMatrixAggregates,
  formatGridNumber,
  generateCustomColumns,
  generateDateTime,
  generateTimeSeriesColumns,
  getAggregateTypes,
} from "../utils";
import {
  AGGREGATE_CONFIG_CASES,
  AGGREGATE_TEST_CASES,
  COLUMN_TEST_CASES,
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
      expect(result).toEqual(expected);
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
        const hours = result.map((dateStr) => {
          const match = dateStr.match(/(\d{2}):00$/);
          return match ? parseInt(match[1], 10) : -1;
        });

        // Verify all hours are consecutive (starting from 00 of current day in UTC)
        expect(hours[0]).toBe(0); // Starts at 00:00 current day in UTC
        for (let i = 1; i < 24; i++) {
          expect(hours[i]).toBe(i);
        }

        // Verify no duplicates
        const uniqueResults = new Set(result);
        expect(uniqueResults.size).toBe(24);
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
