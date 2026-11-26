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
  GridCellKind,
  type DataEditorProps,
  type EditableGridCell,
} from "@glideapps/glide-data-grid";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import DataGridForm from "..";
import type { DataGridFormApi, DataGridFormSubmitData } from "../types";

// The grid is drawn in a canvas: capture its props to trigger edits and deletions directly
let editorProps: DataEditorProps;

vi.mock("@glideapps/glide-data-grid", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@glideapps/glide-data-grid")>()),
  DataEditor: (props: DataEditorProps) => {
    editorProps = props;
    return <div />;
  },
}));

vi.mock("@/hooks/useFormBlocker", () => ({ default: vi.fn() }));
vi.mock("@/hooks/useEnqueueErrorSnackbar", () => ({ default: () => vi.fn() }));

type TestData = Record<string, Record<string, number>>;

const columns = [{ id: "cost", title: "Cost" }];

// Built like an API response (`JSON.parse`): "__proto__" is an own property
function createData() {
  return JSON.parse('{ "__proto__": { "cost": 1 }, "fr": { "cost": 2 } }') as TestData;
}

function numberCell(value: number): EditableGridCell {
  return { kind: GridCellKind.Number, data: value, displayData: String(value), allowOverlay: true };
}

function getSaveButton() {
  return screen.getByRole("button", { name: "global.save" });
}

function renderForm(props: {
  onSubmit?: (data: DataGridFormSubmitData<TestData>) => void | Promise<void>;
  allowRowDeletion?: boolean;
}) {
  const onSubmit = vi.fn(props.onSubmit);
  const apiRef = createRef<DataGridFormApi<TestData>>();

  render(
    <DataGridForm
      defaultData={createData()}
      columns={columns}
      onSubmit={onSubmit}
      apiRef={apiRef}
      allowRowDeletion={props.allowRowDeletion}
    />,
  );

  return {
    getApi: () => {
      if (!apiRef.current) {
        throw new Error("DataGridForm API is not set");
      }
      return apiRef.current;
    },
    // Data passed to the last `onSubmit` call
    getSubmitData: () => onSubmit.mock.lastCall?.[0] as DataGridFormSubmitData<TestData>,
  };
}

describe("DataGridForm changes with row IDs matching Object.prototype keys", () => {
  test("keeps an edited `__proto__` row in `changes.updated`", async () => {
    const { getSubmitData } = renderForm({});

    // Column 0 is the row markers column added by DataGrid
    act(() => {
      editorProps.onCellsEdited?.([{ location: [1, 0], value: numberCell(42) }]);
    });
    await userEvent.click(getSaveButton());

    const { changes, dirtyValues } = getSubmitData();

    expect(Object.hasOwn(changes.updated, "__proto__")).toBe(true);
    expect(changes.updated["__proto__"]).toEqual({ cost: 42 });
    expect(dirtyValues).toBe(changes.updated);
  });

  test("keeps an added `__proto__` row in `changes.added`", async () => {
    const { getApi, getSubmitData } = renderForm({});

    act(() => {
      const { data, setData } = getApi();
      const { ["__proto__"]: _, ...rest } = data;
      // Starts from saved data without the row, then adds it back as a new row
      setData({ ...rest });
    });
    await userEvent.click(getSaveButton());

    act(() => {
      const { data, setData } = getApi();
      setData({ ...data, ["__proto__"]: { cost: 7 } });
    });
    await userEvent.click(getSaveButton());

    const { changes } = getSubmitData();

    expect(Object.hasOwn(changes.added, "__proto__")).toBe(true);
    expect(changes.added["__proto__"]).toEqual({ cost: 7 });
  });

  test("marks a `__proto__` row as saved after a partially failed submit", async () => {
    renderForm({
      onSubmit: ({ markAsSaved }) => {
        markAsSaved("__proto__");
        throw new Error("Failed after saving `__proto__`");
      },
    });

    act(() => {
      editorProps.onCellsEdited?.([{ location: [1, 0], value: numberCell(42) }]);
    });
    await userEvent.click(getSaveButton());

    // The only edited row has been marked as saved: nothing is left to submit
    expect(screen.getByRole("alert")).toHaveTextContent("Failed after saving `__proto__`");
    expect(getSaveButton()).toBeDisabled();
  });

  test("reports a deleted `constructor` row in `changes.deleted`", async () => {
    const { getApi, getSubmitData } = renderForm({ allowRowDeletion: true });

    act(() => {
      const { data, setData } = getApi();
      setData({ ...data, constructor: { cost: 3 } });
    });
    await userEvent.click(getSaveButton());

    // Rows are ordered by insertion: "__proto__", "fr", "constructor"
    act(() => {
      editorProps.onDelete?.({
        rows: CompactSelection.fromSingleSelection(2),
        columns: CompactSelection.empty(),
      });
    });
    await userEvent.click(getSaveButton());

    expect(getSubmitData().changes.deleted).toEqual(["constructor"]);
  });
});
