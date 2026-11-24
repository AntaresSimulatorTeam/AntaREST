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

import { CompactSelection, type GridSelection } from "@glideapps/glide-data-grid";
import { renderHook } from "@testing-library/react";
import { useSelectionStats } from "..";
import { Column } from "../../../shared/constants";
import type { EnhancedGridColumn } from "../../../shared/types";

vi.mock("@/utils/domUtils", () => ({ measureTextWidth: () => 0 }));

const columns: EnhancedGridColumn[] = [
  { id: "date", title: "Date", type: Column.DateTime, editable: false },
  { id: "input", title: "Input", type: Column.Number, editable: true },
  ...["min", "max", "avg"].map((id) => ({
    id,
    title: id,
    type: Column.Aggregate,
    editable: false,
  })),
];

const emptySelection: GridSelection = {
  rows: CompactSelection.empty(),
  columns: CompactSelection.empty(),
};

const values = [
  [undefined, 10, 2, 20, 11],
  [undefined, 30, 5, 40, 22],
  [undefined, 50, 8, 60, 33],
];

test.each([
  [2, { count: 3, sum: 15, average: 5, min: 2, max: 8 }],
  [3, { count: 3, sum: 120, average: 40, min: 20, max: 60 }],
  [4, { count: 3, sum: 66, average: 22, min: 11, max: 33 }],
])("calculates all footer statistics for column %i", (col, expected) => {
  const { result } = renderHook(() =>
    useSelectionStats({
      columns,
      rows: values.length,
      selection: { ...emptySelection, columns: CompactSelection.fromSingleSelection(col) },
      getCellValue: ([x, y]) => values[y][x],
    }),
  );
  expect(result.current).toEqual(expected);
});

test("summarizes only ordinary numbers in native row selections", () => {
  const { result } = renderHook(() =>
    useSelectionStats({
      columns,
      rows: values.length,
      selection: { ...emptySelection, rows: CompactSelection.empty().add(0).add(2) },
      getCellValue: ([x, y]) => values[y][x],
    }),
  );
  expect(result.current).toEqual({ count: 2, sum: 60, average: 30, min: 10, max: 50 });
});

test("uses unrounded values and updates when values change without a new selection", () => {
  const selection = { ...emptySelection, columns: CompactSelection.fromSingleSelection(4) };
  const { result, rerender } = renderHook(
    ({ value }) =>
      useSelectionStats({
        columns,
        rows: 3,
        selection,
        getCellValue: () => value,
      }),
    { initialProps: { value: 1 / 3 } },
  );
  expect(result.current?.sum).toBe(1);
  rerender({ value: 2 / 3 });
  expect(result.current?.sum).toBe(2);
});

test("ignores missing values and clears the footer with selection", () => {
  const { result, rerender } = renderHook(
    ({ selection }) =>
      useSelectionStats({
        columns,
        rows: 3,
        selection,
        getCellValue: ([, row]) => (row === 1 ? undefined : -2),
      }),
    {
      initialProps: {
        selection: { ...emptySelection, columns: CompactSelection.fromSingleSelection(2) },
      },
    },
  );
  expect(result.current).toEqual({ count: 2, sum: -4, average: -2, min: -2, max: -2 });
  rerender({ selection: emptySelection });
  expect(result.current).toBeNull();
});

test("counts overlapping cell ranges once", () => {
  const { result } = renderHook(() =>
    useSelectionStats({
      columns,
      rows: 3,
      selection: {
        ...emptySelection,
        current: {
          cell: [2, 1],
          range: { x: 2, y: 1, width: 1, height: 2 },
          rangeStack: [{ x: 2, y: 0, width: 1, height: 2 }],
        },
      },
      getCellValue: ([x, y]) => values[y][x],
    }),
  );
  expect(result.current).toEqual({ count: 3, sum: 15, average: 5, min: 2, max: 8 });
});
