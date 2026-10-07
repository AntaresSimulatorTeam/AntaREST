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

import { CompactSelection, type GridSelection, type Rectangle } from "@glideapps/glide-data-grid";
import { Column } from "../../../shared/constants";
import type { EnhancedGridColumn } from "../../../shared/types";
import { EMPTY_SELECTION, normalizeSelection } from "../selectionUtils";

vi.mock("@/utils/domUtils", () => ({ measureTextWidth: () => 0 }));

const columns: EnhancedGridColumn[] = [
  { id: "date", title: "Date", type: Column.DateTime, editable: false },
  ...["a", "b"].map((id) => ({ id, title: id, type: Column.Number, editable: true })),
  ...["min", "max", "avg"].map((id) => ({
    id,
    title: id,
    type: Column.Aggregate,
    editable: false,
  })),
];

const selectColumns = (...indices: number[]): GridSelection => ({
  ...EMPTY_SELECTION,
  columns: indices.reduce((result, col) => result.add(col), CompactSelection.empty()),
});

const normalize = (selection: GridSelection, previous = EMPTY_SELECTION) =>
  normalizeSelection({ selection, previous, columns, rows: 3 });

const selectRange = (col: number, range: Rectangle): GridSelection => ({
  ...EMPTY_SELECTION,
  current: { cell: [col, 0], range, rangeStack: [] },
});

test.each([3, 4, 5])("selects aggregate column %i exclusively after a matrix range", (col) => {
  const previous = selectRange(1, { x: 1, y: 0, width: 2, height: 2 });
  expect(normalize(selectColumns(col), previous)).toEqual(selectColumns(col));
});

test.each([
  [[1], [1, 3], [3]], // Ctrl/Cmd: data -> aggregate
  [[3], [1, 3], [1]], // Ctrl/Cmd: aggregate -> data
  [[3], [3, 4], [4]], // Ctrl/Cmd: aggregate -> aggregate
  [[1], [1, 2, 3, 4, 5], [5]], // Shift to the right
  [[5], [3, 4, 5], [3]], // Shift to the left
  [[5], [1, 2, 3, 4, 5], [1, 2]], // Shift back into matrix
  [[1], [1, 2], [1, 2]], // ordinary multi-column selection
  [[3], [], []], // deselect an aggregate
])("normalizes column selection from %j to %j", (before, next, expected) => {
  expect([...normalize(selectColumns(...next), selectColumns(...before)).columns]).toEqual(
    expected,
  );
});

test("clamps a matrix range at the aggregate boundary", () => {
  const selection = normalize(selectRange(2, { x: 1, y: 0, width: 4, height: 2 }));
  expect(selection.current?.range).toEqual({ x: 1, y: 0, width: 2, height: 2 });
});

test.each([3, 4, 5])("keeps a range anchored in aggregate %i within that column", (col) => {
  const selection = normalize(selectRange(col, { x: 1, y: 0, width: 5, height: 2 }));
  expect(selection.current?.range).toEqual({ x: col, y: 0, width: 1, height: 2 });
});

test.each([
  [1, { x: 0, y: 0, width: 3, height: 3 }],
  [3, { x: 3, y: 0, width: 1, height: 3 }],
  [4, { x: 4, y: 0, width: 1, height: 3 }],
  [5, { x: 5, y: 0, width: 1, height: 3 }],
])("keeps full-grid selections in the domain of focused column %i", (col, expectedRange) => {
  const selection = normalize({
    ...EMPTY_SELECTION,
    current: {
      cell: [col, 2],
      range: { x: 0, y: 0, width: 6, height: 3 },
      rangeStack: [],
    },
  });
  expect(selection.current?.range).toEqual(expectedRange);
  expect(selection.current?.cell).toEqual([col, 2]);
});

test("preserves native row selection and clears an aggregate", () => {
  const rows = { ...EMPTY_SELECTION, rows: CompactSelection.empty().add(0).add(2) };
  expect(normalize(rows, selectColumns(3))).toEqual(rows);
});

test("clears selection on Escape", () => {
  expect(normalize(EMPTY_SELECTION, selectColumns(4))).toEqual(EMPTY_SELECTION);
});

test("does not change selection behavior for matrices without aggregates", () => {
  const selection = selectRange(0, { x: 0, y: 0, width: 3, height: 3 });
  expect(
    normalizeSelection({
      selection,
      previous: EMPTY_SELECTION,
      columns: columns.slice(0, 3),
      rows: 3,
    }),
  ).toBe(selection);
});
