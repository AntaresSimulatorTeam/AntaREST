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
import { Column } from "./types";
import {
  calculateMatrixAggregates,
  formatNumber,
  generateDateTime,
  generateTimeSeriesColumns,
} from "./utils";

describe("generateDateTime", () => {
  test("generates correct number of dates", () => {
    const metadata: MatrixIndex = {
      start_date: "2023-01-01T00:00:00Z",
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
