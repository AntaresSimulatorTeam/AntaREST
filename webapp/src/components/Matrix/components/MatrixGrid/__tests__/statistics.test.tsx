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

import {
  CompactSelection,
  DataEditor,
  GridCellKind,
  type DataEditorProps,
  type GridSelection,
} from "@glideapps/glide-data-grid";
import { act, render, screen } from "@testing-library/react";
import MatrixGrid, { type MatrixGridProps } from "..";
import { MatrixContext, type MatrixContextValue } from "../../../context/MatrixContext";
import { Column } from "../../../shared/constants";
import type { EnhancedGridColumn, NonEmptyMatrix } from "../../../shared/types";
import { calculateMatrixAggregates } from "../../../shared/utils";
import { EMPTY_SELECTION } from "../selectionUtils";

vi.mock("@/utils/domUtils", () => ({ measureTextWidth: () => 0 }));
let editorProps: DataEditorProps;
vi.mock("@glideapps/glide-data-grid", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@glideapps/glide-data-grid")>()),
  DataEditor: vi.fn((props: DataEditorProps) => {
    editorProps = props;
    return <div data-testid="editor" />;
  }),
}));

const data: NonEmptyMatrix = [
  [2, 20],
  [5, 40],
  [8, 60],
];

const columns: EnhancedGridColumn[] = [
  { id: "row", title: "Row", type: Column.Text, editable: false },
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
  columns: indices.reduce((selected, col) => selected.add(col), CompactSelection.empty()),
});

const select = (selection: GridSelection) =>
  act(() => editorProps.onGridSelectionChange?.(selection));

const expectStats = (stats: Record<string, string>) => {
  for (const [label, value] of Object.entries(stats)) {
    expect(screen.getByText(label, { exact: true }).nextElementSibling?.textContent).toBe(value);
  }
};

const context: MatrixContextValue = {
  currentState: { data, aggregates: {} },
  isSubmitting: false,
  updateCount: 0,
  aggregateTypes: [],
  setMatrixData: vi.fn(),
  undo: vi.fn(),
  redo: vi.fn(),
  canUndo: false,
  canRedo: false,
  isDirty: false,
  filterPreview: { active: false, criteria: { rowsIndices: [0, 1, 2], columnsIndices: [0, 1] } },
  setFilterPreview: vi.fn(),
};

function Grid({
  matrix = data,
  columns: gridColumns = columns,
  rows = matrix.length,
  filterPreview = context.filterPreview,
}: {
  matrix?: NonEmptyMatrix;
  columns?: MatrixGridProps["columns"];
  rows?: number;
  filterPreview?: MatrixContextValue["filterPreview"];
}) {
  return (
    <MatrixContext.Provider value={{ ...context, filterPreview }}>
      <MatrixGrid
        data={matrix}
        rows={rows}
        columns={gridColumns}
        aggregates={calculateMatrixAggregates({ matrix, types: ["min", "max", "avg"] })}
      />
    </MatrixContext.Provider>
  );
}

test("keeps the rendered selection and footer synchronized when changing selection domains", () => {
  render(<Grid />);
  select(selectColumns(3));
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([3]);
  expectStats({ Nb: "3", Total: "15", Avg: "5", Min: "2", Max: "8" });

  select(selectColumns(3, 4));
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([4]);
  expectStats({ Nb: "3", Total: "120", Avg: "40", Min: "20", Max: "60" });

  select(selectColumns(1, 4));
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([1]);
  expectStats({ Nb: "3", Total: "15" });

  select(selectColumns(1, 2));
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([1, 2]);
  expectStats({ Nb: "6", Total: "135" });
});

test("uses displayed source rows and columns for aggregate, ordinary, and row statistics under filtering", () => {
  render(
    <Grid
      filterPreview={{ active: true, criteria: { rowsIndices: [2, 0], columnsIndices: [1] } }}
    />,
  );
  select(selectColumns(2)); // Min follows the single visible data column.
  expectStats({ Nb: "2", Total: "10", Avg: "5", Min: "2", Max: "8" });
  expect(editorProps.getCellContent([2, 0])).toMatchObject({ kind: GridCellKind.Number, data: 8 });

  select(selectColumns(1));
  expectStats({ Nb: "2", Total: "80", Avg: "40" });
  select({ ...EMPTY_SELECTION, rows: CompactSelection.fromSingleSelection(0) });
  expectStats({ Nb: "1", Total: "60" });
});

test("preserves selection and recalculates statistics after edits, undo, and equivalent layouts", () => {
  const { rerender } = render(<Grid />);
  select(selectColumns(3));
  rerender(
    <Grid
      matrix={[
        [12, 20],
        [5, 40],
        [8, 60],
      ]}
    />,
  );
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([3]);
  expectStats({ Nb: "3", Total: "25", Min: "5", Max: "12" });
  rerender(<Grid columns={columns.map((column) => ({ ...column }))} />); // Undo / restored values.
  expect([...(editorProps.gridSelection?.columns ?? [])]).toEqual([3]);
  expectStats({ Total: "15" });
});

test.each([
  {
    change: "filtered rows with the same count",
    before: (
      <Grid
        filterPreview={{ active: true, criteria: { rowsIndices: [0, 1], columnsIndices: [0, 1] } }}
      />
    ),
    after: (
      <Grid
        filterPreview={{ active: true, criteria: { rowsIndices: [1, 2], columnsIndices: [0, 1] } }}
      />
    ),
  },
  {
    change: "filtered columns with the same count",
    before: (
      <Grid
        filterPreview={{ active: true, criteria: { rowsIndices: [0, 1, 2], columnsIndices: [0] } }}
      />
    ),
    after: (
      <Grid
        filterPreview={{ active: true, criteria: { rowsIndices: [0, 1, 2], columnsIndices: [1] } }}
      />
    ),
  },
  { change: "row count", before: <Grid />, after: <Grid rows={2} /> },
  { change: "column count", before: <Grid />, after: <Grid columns={columns.slice(0, -1)} /> },
])("clears selection before rendering changes to $change", ({ before, after }) => {
  const { rerender } = render(before);
  select(selectColumns(3));
  expect(editorProps.gridSelection?.columns.hasIndex(3)).toBe(true);

  vi.mocked(DataEditor).mockClear();
  rerender(after);

  expect(DataEditor).toHaveBeenCalled();
  for (const [props] of vi.mocked(DataEditor).mock.calls) {
    expect(props.gridSelection).toEqual(EMPTY_SELECTION);
  }
  expectStats({ Nb: "0", Total: "0" });

  rerender(before);
  expect(editorProps.gridSelection).toEqual(EMPTY_SELECTION);
  expectStats({ Nb: "0", Total: "0" });
});
