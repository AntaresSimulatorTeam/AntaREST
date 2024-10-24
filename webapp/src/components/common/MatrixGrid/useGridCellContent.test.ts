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

import { renderHook } from "@testing-library/react";
import { useGridCellContent } from "./useGridCellContent";
import {
  Column,
  type ColumnType,
  type MatrixAggregates,
  type EnhancedGridColumn,
} from "./types";
import { useColumnMapping } from "./useColumnMapping";
import { type Item } from "@glideapps/glide-data-grid";

describe("useGridCellContent", () => {
  // Test data factories
  const createColumn = (
    id: string,
    type: ColumnType,
    editable = false,
  ): EnhancedGridColumn => ({
    id,
    title: id.charAt(0).toUpperCase() + id.slice(1),
    type,
    width: type === Column.DateTime ? 150 : 50,
    editable,
  });

  const createCoordinate = (col: number, row: number): Item =>
    [col, row] as Item;

  interface RenderOptions {
    data: number[][];
    columns: EnhancedGridColumn[];
    dateTime?: string[];
    aggregates?: MatrixAggregates;
    rowHeaders?: string[];
  }

  const renderGridCellContent = ({
    data,
    columns,
    dateTime,
    aggregates,
    rowHeaders,
  }: RenderOptions) => {
    const { result: mappingResult } = renderHook(() =>
      useColumnMapping(columns),
    );

    const { gridToData } = mappingResult.current;

    const { result } = renderHook(() =>
      useGridCellContent(
        data,
        columns,
        gridToData,
        dateTime,
        aggregates,
        rowHeaders,
      ),
    );

    return result.current;
  };

  const assertNumberCell = (
    cell: ReturnType<ReturnType<typeof renderGridCellContent>>,
    expectedValue: number | undefined,
    message: string,
  ) => {
    if (cell.kind === "number" && "data" in cell) {
      expect(cell.data).toBe(expectedValue);
    } else {
      throw new Error(message);
    }
  };

  const assertTextCell = (
    cell: ReturnType<ReturnType<typeof renderGridCellContent>>,
    expectedValue: string,
    message: string,
  ) => {
    if (cell.kind === "text" && "displayData" in cell) {
      expect(cell.displayData).toBe(expectedValue);
    } else {
      throw new Error(message);
    }
  };

  describe("Aggregate columns", () => {
    const DATA = {
      columns: [createColumn("total", Column.Aggregate)],
      data: [
        [10, 20, 30],
        [15, 25, 35],
        [5, 15, 25],
      ],
      aggregates: {
        min: [5, 15, 25],
        max: [15, 25, 35],
        avg: [10, 20, 30],
        total: [30, 60, 90],
      },
    };

    test.each([
      [0, 30],
      [1, 60],
      [2, 90],
    ])("returns correct aggregate for row %i", (row, expected) => {
      const getCellContent = renderGridCellContent(DATA);
      const cell = getCellContent(createCoordinate(0, row));
      assertNumberCell(
        cell,
        expected,
        `Expected aggregate value ${expected} at row ${row}`,
      );
    });
  });

  describe("Mixed column types", () => {
    const DATA = {
      columns: [
        createColumn("rowHeader", Column.Text),
        createColumn("date", Column.DateTime),
        createColumn("data1", Column.Number, true),
        createColumn("data2", Column.Number, true),
        createColumn("total", Column.Aggregate),
      ],
      data: [
        [100, 200],
        [150, 250],
      ],
      dateTime: ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
      rowHeaders: ["Row 1", "Row 2"],
      aggregates: {
        min: [100, 200],
        max: [150, 250],
        avg: [125, 225],
        total: [250, 450],
      },
    };

    test("handles all column types correctly", () => {
      const getCellContent = renderGridCellContent(DATA);

      // Text column (Row header)
      assertTextCell(
        getCellContent(createCoordinate(0, 0)),
        "Row 1",
        "Expected row header text",
      );

      // Number columns
      assertNumberCell(
        getCellContent(createCoordinate(2, 0)),
        100,
        "Expected first data column value",
      );
      assertNumberCell(
        getCellContent(createCoordinate(3, 0)),
        200,
        "Expected second data column value",
      );

      // Aggregate column
      assertNumberCell(
        getCellContent(createCoordinate(4, 0)),
        250,
        "Expected aggregate value",
      );
    });
  });

  describe("Edge cases", () => {
    test("handles empty data array", () => {
      const options = {
        columns: [createColumn("data1", Column.Number, true)],
        data: [],
      };

      const getCellContent = renderGridCellContent(options);
      const cell = getCellContent(createCoordinate(0, 0));
      assertNumberCell(cell, undefined, "Expected undefined for empty data");
    });

    test("handles out of bounds access", () => {
      const options = {
        columns: [createColumn("data1", Column.Number, true)],
        data: [[100]],
      };

      const getCellContent = renderGridCellContent(options);

      // Column out of bounds
      const colCell = getCellContent(createCoordinate(1, 0));
      assertTextCell(colCell, "N/A", "Expected N/A for column out of bounds");

      // Row out of bounds
      const rowCell = getCellContent(createCoordinate(0, 1));
      assertNumberCell(
        rowCell,
        undefined,
        "Expected undefined for row out of bounds",
      );
    });
  });

  describe("Number formatting", () => {
    const formatTestCases = [
      {
        desc: "formats regular numbers",
        value: 1234567.89,
        expected: "1 234 567.89",
      },
      {
        desc: "handles very large numbers",
        value: 1e20,
        expected: "100 000 000 000 000 000 000",
      },
      {
        desc: "handles very small numbers",
        value: 0.00001,
        expected: "0.00001",
      },
      {
        desc: "handles negative numbers",
        value: -1234567.89,
        expected: "-1 234 567.89",
      },
      {
        desc: "handles zero",
        value: 0,
        expected: "0",
      },
    ];

    test.each(formatTestCases)("$desc", ({ value, expected }) => {
      const options = {
        columns: [createColumn("number", Column.Number, true)],
        data: [[value]],
      };

      const getCellContent = renderGridCellContent(options);
      const cell = getCellContent(createCoordinate(0, 0));

      if (cell.kind === "number" && "data" in cell) {
        expect(cell.data).toBe(value);
        expect(cell.displayData).toBe(expected);
      } else {
        throw new Error(`Expected formatted number cell for value ${value}`);
      }
    });
  });
});
