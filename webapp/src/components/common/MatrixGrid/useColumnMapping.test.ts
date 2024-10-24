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
import { useColumnMapping } from "./useColumnMapping";
import { EnhancedGridColumn, Column } from "./types";
import type { ColumnType } from "./types";
import { Item } from "@glideapps/glide-data-grid";

describe("useColumnMapping", () => {
  // Test data factories
  const createColumn = (
    id: string,
    type: ColumnType,
    editable = false,
  ): EnhancedGridColumn => ({
    id,
    title: id.charAt(0).toUpperCase() + id.slice(1),
    type,
    width: 100,
    editable,
  });

  const createNumericColumn = (id: string) =>
    createColumn(id, Column.Number, true);

  const COLUMNS = {
    mixed: [
      createColumn("text", Column.Text),
      createColumn("date", Column.DateTime),
      createNumericColumn("num1"),
      createNumericColumn("num2"),
      createColumn("agg", Column.Aggregate),
    ],
    nonData: [
      createColumn("text", Column.Text),
      createColumn("date", Column.DateTime),
    ],
    dataOnly: [createNumericColumn("num1"), createNumericColumn("num2")],
  };

  // Helper function to create properly typed coordinates
  const createCoordinate = (col: number, row: number): Item =>
    [col, row] as Item;

  // Helper function to render the hook
  const renderColumnMapping = (columns: EnhancedGridColumn[]) =>
    renderHook(() => useColumnMapping(columns));

  describe("hook initialization", () => {
    test("should create mapping functions", () => {
      const { result } = renderColumnMapping(COLUMNS.mixed);

      expect(result.current.gridToData).toBeInstanceOf(Function);
      expect(result.current.dataToGrid).toBeInstanceOf(Function);
    });

    test("should memoize the result", () => {
      const { result, rerender } = renderHook(
        (props) => useColumnMapping(props.columns),
        { initialProps: { columns: COLUMNS.mixed } },
      );

      const initialResult = result.current;
      rerender({ columns: COLUMNS.mixed });
      expect(result.current).toBe(initialResult);
    });
  });

  describe("gridToData mapping", () => {
    describe("with mixed columns", () => {
      test("should return null for non-data columns", () => {
        const { result } = renderColumnMapping(COLUMNS.mixed);

        const nonDataCoordinates: Item[] = [
          createCoordinate(0, 0), // Text column
          createCoordinate(1, 0), // DateTime column
          createCoordinate(4, 0), // Aggregate column
        ];

        nonDataCoordinates.forEach((coord) => {
          expect(result.current.gridToData(coord)).toBeNull();
        });
      });

      test("should map data columns correctly", () => {
        const { result } = renderColumnMapping(COLUMNS.mixed);

        const mappings = [
          { grid: createCoordinate(2, 0), expected: createCoordinate(0, 0) }, // First Number column
          { grid: createCoordinate(3, 1), expected: createCoordinate(1, 1) }, // Second Number column
        ];

        mappings.forEach(({ grid, expected }) => {
          expect(result.current.gridToData(grid)).toEqual(expected);
        });
      });
    });

    describe("with specific column configurations", () => {
      test("should handle non-data columns only", () => {
        const { result } = renderColumnMapping(COLUMNS.nonData);
        const coord = createCoordinate(0, 0);

        expect(result.current.gridToData(coord)).toBeNull();
        expect(result.current.gridToData(createCoordinate(1, 0))).toBeNull();
        expect(result.current.dataToGrid(coord)).toEqual([undefined, 0]);
      });

      test("should handle data columns only", () => {
        const { result } = renderColumnMapping(COLUMNS.dataOnly);

        const mappings = [
          { grid: createCoordinate(0, 0), data: createCoordinate(0, 0) },
          { grid: createCoordinate(1, 1), data: createCoordinate(1, 1) },
        ];

        mappings.forEach(({ grid, data }) => {
          expect(result.current.gridToData(grid)).toEqual(data);
          expect(result.current.dataToGrid(data)).toEqual(grid);
        });
      });
    });
  });

  describe("dataToGrid mapping", () => {
    test("should map data coordinates to grid coordinates", () => {
      const { result } = renderColumnMapping(COLUMNS.mixed);
      const mappings = [
        { data: createCoordinate(0, 0), expected: createCoordinate(2, 0) }, // First data column
        { data: createCoordinate(1, 1), expected: createCoordinate(3, 1) }, // Second data column
      ];

      mappings.forEach(({ data, expected }) => {
        expect(result.current.dataToGrid(data)).toEqual(expected);
      });
    });
  });
});
