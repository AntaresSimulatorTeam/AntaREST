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

import { renderHook } from "@testing-library/react";
import { FILTER_OPERATORS, FILTER_TYPES } from "../../constants";
import type { FilterState } from "../../types";
import { useFilteredData } from "../useFilteredData";

describe("useFilteredData", () => {
  const defaultFilter: FilterState = {
    active: true,
    columnsFilter: {
      type: FILTER_TYPES.LIST,
      list: [],
      operator: FILTER_OPERATORS.EQUALS,
    },
    rowsFilters: [],
    operation: {
      type: "Eq",
      value: 0,
    },
  };

  describe("Empty Filter Behavior", () => {
    it("should return all columns when column list filter is empty", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [], // Empty list
          operator: FILTER_OPERATORS.EQUALS,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 10,
          columnCount: 5,
        }),
      );

      expect(result.current.columnsIndices).toEqual([0, 1, 2, 3, 4]);
      expect(result.current.rowsIndices).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    });

    it("should return all indices when filter is inactive", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: false, // Filter is inactive
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [1, 2], // Has selections but filter is inactive
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 10,
          columnCount: 5,
        }),
      );

      expect(result.current.columnsIndices).toEqual([0, 1, 2, 3, 4]);
      expect(result.current.rowsIndices).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    });

    it("should handle empty column list with different operators", () => {
      const operators = [
        FILTER_OPERATORS.EQUALS,
        FILTER_OPERATORS.GREATER_THAN,
        FILTER_OPERATORS.LESS_THAN,
        FILTER_OPERATORS.RANGE,
      ];

      operators.forEach((operator) => {
        const filter: FilterState = {
          ...defaultFilter,
          active: true,
          columnsFilter: {
            type: FILTER_TYPES.LIST,
            list: [],
            operator,
          },
        };

        const { result } = renderHook(() =>
          useFilteredData({
            filter,
            datesInfo: undefined,
            isTimeSeries: false,
            timeFrequency: undefined,
            rowCount: 5,
            columnCount: 3,
          }),
        );

        expect(result.current.columnsIndices).toEqual([0, 1, 2]);
      });
    });

    it("should filter columns when list is not empty", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [2, 4], // Select columns 2 and 4 (1-based)
          operator: FILTER_OPERATORS.EQUALS,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 5,
        }),
      );

      expect(result.current.columnsIndices).toEqual([1, 3]); // 0-based indices
    });

    it("should handle range filters correctly", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.RANGE,
          range: { min: 2, max: 4 }, // Columns 2-4 (1-based)
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 6,
        }),
      );

      expect(result.current.columnsIndices).toEqual([1, 2, 3]); // 0-based indices
    });

    it("should handle greater than operator with single value", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [3], // Greater than column 3
          operator: FILTER_OPERATORS.GREATER_THAN,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 6,
        }),
      );

      expect(result.current.columnsIndices).toEqual([3, 4, 5]); // Columns 4, 5, 6 (0-based: 3, 4, 5)
    });

    it("should handle less than operator with single value", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [4], // Less than column 4
          operator: FILTER_OPERATORS.LESS_THAN,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 6,
        }),
      );

      expect(result.current.columnsIndices).toEqual([0, 1, 2]); // Columns 1, 2, 3 (0-based: 0, 1, 2)
    });

    it("should handle range operator with list values", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [2, 5], // Range between 2 and 5
          operator: FILTER_OPERATORS.RANGE,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 7,
        }),
      );

      expect(result.current.columnsIndices).toEqual([1, 2, 3, 4]); // Columns 2, 3, 4, 5 (0-based: 1, 2, 3, 4)
    });

    it("should handle invalid column indices gracefully", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.LIST,
          list: [0, 10, 20], // Some indices out of bounds
          operator: FILTER_OPERATORS.EQUALS,
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 5,
        }),
      );

      expect(result.current.columnsIndices).toEqual([]); // No valid indices
    });

    it("should return empty range when range filter has no range defined", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.RANGE,
          range: undefined, // No range defined
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 5,
          columnCount: 5,
        }),
      );

      expect(result.current.columnsIndices).toEqual([]);
    });
  });

  describe("Edge Cases", () => {
    it("should handle zero rows and columns", () => {
      const { result } = renderHook(() =>
        useFilteredData({
          filter: defaultFilter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 0,
          columnCount: 0,
        }),
      );

      expect(result.current.columnsIndices).toEqual([]);
      expect(result.current.rowsIndices).toEqual([]);
    });

    it("should handle large datasets efficiently", () => {
      const filter: FilterState = {
        ...defaultFilter,
        active: true,
        columnsFilter: {
          type: FILTER_TYPES.RANGE,
          range: { min: 100, max: 200 },
        },
      };

      const { result } = renderHook(() =>
        useFilteredData({
          filter,
          datesInfo: undefined,
          isTimeSeries: false,
          timeFrequency: undefined,
          rowCount: 1000,
          columnCount: 500,
        }),
      );

      expect(result.current.columnsIndices).toHaveLength(101); // 100 to 200 inclusive
      expect(result.current.columnsIndices[0]).toBe(99); // 0-based index
      expect(result.current.columnsIndices[100]).toBe(199); // 0-based index
    });
  });
});
