import { renderHook } from "@testing-library/react";
import { describe, test, expect } from "vitest";
import { useColumnMapping } from "./useColumnMapping";
import { EnhancedGridColumn } from "./types";
import { ColumnDataType } from "./utils";

describe("useColumnMapping", () => {
  const testColumns: EnhancedGridColumn[] = [
    {
      id: "text",
      title: "Text",
      type: ColumnDataType.Text,
      width: 100,
      editable: false,
    },
    {
      id: "date",
      title: "Date",
      type: ColumnDataType.DateTime,
      width: 100,
      editable: false,
    },
    {
      id: "num1",
      title: "Number 1",
      type: ColumnDataType.Number,
      width: 100,
      editable: true,
    },
    {
      id: "num2",
      title: "Number 2",
      type: ColumnDataType.Number,
      width: 100,
      editable: true,
    },
    {
      id: "agg",
      title: "Aggregate",
      type: ColumnDataType.Aggregate,
      width: 100,
      editable: false,
    },
  ];

  test("should create gridToData and dataToGrid functions", () => {
    const { result } = renderHook(() => useColumnMapping(testColumns));
    expect(result.current.gridToData).toBeDefined();
    expect(result.current.dataToGrid).toBeDefined();
  });

  describe("gridToData", () => {
    test("should return null for non-data columns", () => {
      const { result } = renderHook(() => useColumnMapping(testColumns));
      expect(result.current.gridToData([0, 0])).toBeNull(); // Text column
      expect(result.current.gridToData([1, 0])).toBeNull(); // DateTime column
      expect(result.current.gridToData([4, 0])).toBeNull(); // Aggregate column
    });

    test("should map grid coordinates to data coordinates for data columns", () => {
      const { result } = renderHook(() => useColumnMapping(testColumns));
      expect(result.current.gridToData([2, 0])).toEqual([0, 0]); // First Number column
      expect(result.current.gridToData([3, 1])).toEqual([1, 1]); // Second Number column
    });
  });

  describe("dataToGrid", () => {
    test("should map data coordinates to grid coordinates", () => {
      const { result } = renderHook(() => useColumnMapping(testColumns));
      expect(result.current.dataToGrid([0, 0])).toEqual([2, 0]); // First data column
      expect(result.current.dataToGrid([1, 1])).toEqual([3, 1]); // Second data column
    });
  });

  test("should handle columns with only non-data types", () => {
    const nonDataColumns: EnhancedGridColumn[] = [
      {
        id: "text",
        title: "Text",
        type: ColumnDataType.Text,
        width: 100,
        editable: false,
      },
      {
        id: "date",
        title: "Date",
        type: ColumnDataType.DateTime,
        width: 100,
        editable: false,
      },
    ];
    const { result } = renderHook(() => useColumnMapping(nonDataColumns));
    expect(result.current.gridToData([0, 0])).toBeNull();
    expect(result.current.gridToData([1, 0])).toBeNull();
    expect(result.current.dataToGrid([0, 0])).toEqual([undefined, 0]); // No data columns, so this should return an invalid grid coordinate
  });

  test("should handle columns with only data types", () => {
    const dataOnlyColumns: EnhancedGridColumn[] = [
      {
        id: "num1",
        title: "Number 1",
        type: ColumnDataType.Number,
        width: 100,
        editable: true,
      },
      {
        id: "num2",
        title: "Number 2",
        type: ColumnDataType.Number,
        width: 100,
        editable: true,
      },
    ];
    const { result } = renderHook(() => useColumnMapping(dataOnlyColumns));
    expect(result.current.gridToData([0, 0])).toEqual([0, 0]);
    expect(result.current.gridToData([1, 1])).toEqual([1, 1]);
    expect(result.current.dataToGrid([0, 0])).toEqual([0, 0]);
    expect(result.current.dataToGrid([1, 1])).toEqual([1, 1]);
  });

  test("should memoize the result", () => {
    const { result, rerender } = renderHook(
      (props) => useColumnMapping(props.columns),
      { initialProps: { columns: testColumns } },
    );
    const initialResult = result.current;
    rerender({ columns: testColumns });
    expect(result.current).toBe(initialResult);
  });
});
