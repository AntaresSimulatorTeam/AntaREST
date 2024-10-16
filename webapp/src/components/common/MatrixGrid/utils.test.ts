/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
  MatrixIndex,
  StudyOutputDownloadLevelDTO,
} from "../../../common/types";
import {
  Aggregate,
  AggregateType,
  Column,
  DateTimeMetadataDTO,
  TimeFrequency,
} from "./types";
import {
  calculateMatrixAggregates,
  formatNumber,
  generateCustomColumns,
  generateDataColumns,
  generateDateTime,
  generateTimeSeriesColumns,
  getAggregateTypes,
} from "./utils";

vi.mock("date-fns", async () => {
  const actual = (await vi.importActual(
    "date-fns",
  )) as typeof import("date-fns");
  return {
    ...actual,
    format: vi.fn((date: Date, formatString: string) => {
      if (formatString.includes("ww")) {
        const weekNumber = actual.getWeek(date);
        return `W ${weekNumber.toString().padStart(2, "0")}`;
      }
      return actual.format(date, formatString);
    }),
  };
});

describe("generateDateTime", () => {
  beforeAll(() => {
    // Set a fixed date for consistent testing
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2023-01-01 00:00:00"));
  });

  it("generates correct annual format", () => {
    const config: DateTimeMetadataDTO = {
      start_date: "2023-01-01 00:00:00",
      steps: 3,
      first_week_size: 7,
      level: TimeFrequency.Annual,
    };
    const result = generateDateTime(config);
    expect(result).toEqual([
      "global.time.annual",
      "global.time.annual",
      "global.time.annual",
    ]);
  });

  it("generates correct monthly format", () => {
    const config: DateTimeMetadataDTO = {
      start_date: "2023-01-01 00:00:00",
      steps: 3,
      first_week_size: 7,
      level: TimeFrequency.Monthly,
    };
    const result = generateDateTime(config);
    expect(result).toEqual(["Jan", "Feb", "Mar"]);
  });

  it("generates correct weekly format with first_week_size 1", () => {
    const config: DateTimeMetadataDTO = {
      start_date: "2023-01-01 00:00:00",
      steps: 3,
      first_week_size: 1,
      level: TimeFrequency.Weekly,
    };
    const result = generateDateTime(config);
    expect(result).toEqual(["W 01", "W 02", "W 03"]);
  });

  it("generates correct daily format", () => {
    const config: DateTimeMetadataDTO = {
      start_date: "2023-01-01 00:00:00",
      steps: 3,
      first_week_size: 7,
      level: TimeFrequency.Daily,
    };
    const result = generateDateTime(config);
    expect(result).toEqual(["Sun 1 Jan", "Mon 2 Jan", "Tue 3 Jan"]);
  });

  it("generates correct hourly format", () => {
    const config: DateTimeMetadataDTO = {
      start_date: "2039-07-01 00:00:00",
      steps: 3,
      first_week_size: 7,
      level: TimeFrequency.Hourly,
    };
    const result = generateDateTime(config);
    expect(result).toEqual([
      "Fri 1 Jul 00:00",
      "Fri 1 Jul 01:00",
      "Fri 1 Jul 02:00",
    ]);
  });

  test("generates correct number of dates", () => {
    const metadata: MatrixIndex = {
      start_date: "2023-01-01 00:00:00",
      steps: 5,
      first_week_size: 7,
      level: StudyOutputDownloadLevelDTO.DAILY,
    };
    const result = generateDateTime(metadata);
    expect(result).toHaveLength(5);
  });
});

describe("generateTimeSeriesColumns", () => {
  test("generates correct number of columns", () => {
    const result = generateTimeSeriesColumns({ count: 5 });
    expect(result).toHaveLength(5);
  });

  test("generates columns with default options", () => {
    const result = generateTimeSeriesColumns({ count: 3 });
    expect(result).toEqual([
      {
        id: "data1",
        title: "TS 1",
        type: Column.Number,
        style: "normal",
        editable: true,
      },
      {
        id: "data2",
        title: "TS 2",
        type: Column.Number,
        style: "normal",
        editable: true,
      },
      {
        id: "data3",
        title: "TS 3",
        type: Column.Number,
        style: "normal",
        editable: true,
      },
    ]);
  });

  test("generates columns with custom options", () => {
    const result = generateTimeSeriesColumns({
      count: 2,
      startIndex: 10,
      prefix: "Data",
      editable: false,
    });
    expect(result).toEqual([
      {
        id: "data10",
        title: "Data 10",
        type: Column.Number,
        style: "normal",
        editable: false,
      },
      {
        id: "data11",
        title: "Data 11",
        type: Column.Number,
        style: "normal",
        editable: false,
      },
    ]);
  });

  test("handles zero count", () => {
    const result = generateTimeSeriesColumns({ count: 0 });
    expect(result).toEqual([]);
  });

  test("handles large count", () => {
    const result = generateTimeSeriesColumns({ count: 1000 });
    expect(result).toHaveLength(1000);
    expect(result[999].id).toBe("data1000");
    expect(result[999].title).toBe("TS 1000");
  });

  test("maintains consistent type and style", () => {
    const result = generateTimeSeriesColumns({ count: 1000 });
    result.forEach((column) => {
      expect(column.type).toBe(Column.Number);
      expect(column.style).toBe("normal");
    });
  });
});

describe("calculateMatrixAggregates", () => {
  it("should calculate correct aggregates for a simple matrix", () => {
    const matrix = [
      [1, 2, 3],
      [4, 5, 6],
      [7, 8, 9],
    ];
    const result = calculateMatrixAggregates(matrix, [
      "min",
      "max",
      "avg",
      "total",
    ]);

    expect(result.min).toEqual([1, 4, 7]);
    expect(result.max).toEqual([3, 6, 9]);
    expect(result.avg).toEqual([2, 5, 8]);
    expect(result.total).toEqual([6, 15, 24]);
  });

  it("should handle decimal numbers correctly by rounding", () => {
    const matrix = [
      [1.1, 2.2, 3.3],
      [4.4, 5.5, 6.6],
    ];
    const result = calculateMatrixAggregates(matrix, [
      "min",
      "max",
      "avg",
      "total",
    ]);

    expect(result.min).toEqual([1.1, 4.4]);
    expect(result.max).toEqual([3.3, 6.6]);
    expect(result.avg).toEqual([2, 6]);
    expect(result.total).toEqual([7, 17]);
  });

  it("should handle negative numbers", () => {
    const matrix = [
      [-1, -2, -3],
      [-4, 0, 4],
    ];
    const result = calculateMatrixAggregates(matrix, [
      "min",
      "max",
      "avg",
      "total",
    ]);

    expect(result.min).toEqual([-3, -4]);
    expect(result.max).toEqual([-1, 4]);
    expect(result.avg).toEqual([-2, 0]);
    expect(result.total).toEqual([-6, 0]);
  });

  it("should handle single-element rows", () => {
    const matrix = [[1], [2], [3]];
    const result = calculateMatrixAggregates(matrix, [
      "min",
      "max",
      "avg",
      "total",
    ]);

    expect(result.min).toEqual([1, 2, 3]);
    expect(result.max).toEqual([1, 2, 3]);
    expect(result.avg).toEqual([1, 2, 3]);
    expect(result.total).toEqual([1, 2, 3]);
  });

  it("should handle large numbers", () => {
    const matrix = [
      [1000000, 2000000, 3000000],
      [4000000, 5000000, 6000000],
    ];
    const result = calculateMatrixAggregates(matrix, [
      "min",
      "max",
      "avg",
      "total",
    ]);

    expect(result.min).toEqual([1000000, 4000000]);
    expect(result.max).toEqual([3000000, 6000000]);
    expect(result.avg).toEqual([2000000, 5000000]);
    expect(result.total).toEqual([6000000, 15000000]);
  });

  it("should round average correctly", () => {
    const matrix = [
      [1, 2, 4],
      [10, 20, 39],
    ];
    const result = calculateMatrixAggregates(matrix, ["avg"]);

    expect(result.avg).toEqual([2, 23]);
  });
});

describe("formatNumber", () => {
  test("formats numbers correctly", () => {
    expect(formatNumber(1234567.89)).toBe("1 234 567.89");
    expect(formatNumber(1000000)).toBe("1 000 000");
    expect(formatNumber(1234.5678)).toBe("1 234.5678");
    expect(formatNumber(undefined)).toBe("");
  });

  test("handles edge cases", () => {
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(-1234567.89)).toBe("-1 234 567.89");
    expect(formatNumber(0.00001)).toBe("0.00001");
    expect(formatNumber(1e20)).toBe("100 000 000 000 000 000 000");
  });
});

describe("generateCustomColumns", () => {
  it("should generate custom columns with correct properties", () => {
    const titles = ["Custom 1", "Custom 2", "Custom 3"];
    const width = 100;
    const result = generateCustomColumns({ titles, width });

    expect(result).toHaveLength(3);
    result.forEach((column, index) => {
      expect(column).toEqual({
        id: `custom${index + 1}`,
        title: titles[index],
        type: Column.Number,
        style: "normal",
        width: 100,
        editable: true,
      });
    });
  });

  it("should handle empty titles array", () => {
    const result = generateCustomColumns({ titles: [], width: 100 });
    expect(result).toEqual([]);
  });
});

describe("generateDataColumns", () => {
  it("should generate custom columns when provided", () => {
    const customColumns = ["Custom 1", "Custom 2"];
    const result = generateDataColumns(false, 5, customColumns, 100);

    expect(result).toHaveLength(2);
    expect(result[0].title).toBe("Custom 1");
    expect(result[1].title).toBe("Custom 2");
  });

  it("should generate time series columns when enabled", () => {
    const result = generateDataColumns(true, 3);

    expect(result).toHaveLength(3);
    expect(result[0].title).toBe("TS 1");
    expect(result[1].title).toBe("TS 2");
    expect(result[2].title).toBe("TS 3");
  });

  it("should return empty array when custom columns not provided and time series disabled", () => {
    const result = generateDataColumns(false, 5);
    expect(result).toEqual([]);
  });
});

describe("getAggregateTypes", () => {
  it('should return correct aggregate types for "stats" config', () => {
    const result = getAggregateTypes("stats");
    expect(result).toEqual([Aggregate.Avg, Aggregate.Min, Aggregate.Max]);
  });

  it('should return correct aggregate types for "all" config', () => {
    const result = getAggregateTypes("all");
    expect(result).toEqual([
      Aggregate.Min,
      Aggregate.Max,
      Aggregate.Avg,
      Aggregate.Total,
    ]);
  });

  it("should return provided aggregate types for array config", () => {
    const config: AggregateType[] = [Aggregate.Min, Aggregate.Max];
    const result = getAggregateTypes(config);
    expect(result).toEqual(config);
  });

  it("should return empty array for invalid config", () => {
    // @ts-expect-error : we are testing an invalid value
    const result = getAggregateTypes("invalid");
    expect(result).toEqual([]);
  });
});

describe("calculateMatrixAggregates", () => {
  const matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
  ];

  it("should calculate min aggregate correctly", () => {
    const result = calculateMatrixAggregates(matrix, [Aggregate.Min]);
    expect(result).toEqual({ min: [1, 4, 7] });
  });

  it("should calculate max aggregate correctly", () => {
    const result = calculateMatrixAggregates(matrix, [Aggregate.Max]);
    expect(result).toEqual({ max: [3, 6, 9] });
  });

  it("should calculate avg aggregate correctly", () => {
    const result = calculateMatrixAggregates(matrix, [Aggregate.Avg]);
    expect(result).toEqual({ avg: [2, 5, 8] });
  });

  it("should calculate total aggregate correctly", () => {
    const result = calculateMatrixAggregates(matrix, [Aggregate.Total]);
    expect(result).toEqual({ total: [6, 15, 24] });
  });

  it("should calculate multiple aggregates correctly", () => {
    const result = calculateMatrixAggregates(matrix, [
      Aggregate.Min,
      Aggregate.Max,
      Aggregate.Avg,
      Aggregate.Total,
    ]);
    expect(result).toEqual({
      min: [1, 4, 7],
      max: [3, 6, 9],
      avg: [2, 5, 8],
      total: [6, 15, 24],
    });
  });

  it("should handle empty matrix", () => {
    const result = calculateMatrixAggregates(
      [],
      [Aggregate.Min, Aggregate.Max, Aggregate.Avg, Aggregate.Total],
    );
    expect(result).toEqual({});
  });
});

describe("formatNumber", () => {
  it("should format integer numbers correctly", () => {
    expect(formatNumber(1234567)).toBe("1 234 567");
    expect(formatNumber(1000000)).toBe("1 000 000");
    expect(formatNumber(1)).toBe("1");
  });

  it("should format decimal numbers correctly", () => {
    expect(formatNumber(1234.56)).toBe("1 234.56");
    expect(formatNumber(1000000.123)).toBe("1 000 000.123");
  });

  it("should handle negative numbers", () => {
    expect(formatNumber(-1234567)).toBe("-1 234 567");
    expect(formatNumber(-1234.56)).toBe("-1 234.56");
  });

  it("should handle zero", () => {
    expect(formatNumber(0)).toBe("0");
  });

  it("should handle undefined", () => {
    expect(formatNumber(undefined)).toBe("");
  });

  it("should handle large numbers", () => {
    expect(formatNumber(1e15)).toBe("1 000 000 000 000 000");
  });
});
