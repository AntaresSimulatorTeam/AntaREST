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

import { CompactSelection, GridCellKind, type DataEditorProps } from "@glideapps/glide-data-grid";
import { act, render } from "@testing-library/react";
import DataGrid from "..";

let editorProps: DataEditorProps;
vi.mock("@glideapps/glide-data-grid", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@glideapps/glide-data-grid")>()),
  DataEditor: (props: DataEditorProps) => {
    editorProps = props;
    return <div />;
  },
}));

test("retains internal selection for uncontrolled DataGrid consumers", () => {
  const onSelectionChange = vi.fn();
  render(
    <DataGrid
      columns={[
        { id: "a", title: "A" },
        { id: "b", title: "B" },
        { id: "c", title: "C" },
      ]}
      rows={3}
      getCellContent={() => ({
        kind: GridCellKind.Text,
        data: "",
        displayData: "",
        allowOverlay: false,
      })}
      onGridSelectionChange={onSelectionChange}
    />,
  );
  const selection = {
    rows: CompactSelection.empty(),
    columns: CompactSelection.empty().add(1).add(2),
  };
  act(() => editorProps.onGridSelectionChange?.(selection));
  expect(editorProps.gridSelection).toEqual(selection);
  expect(onSelectionChange).toHaveBeenCalledWith(selection);
});
