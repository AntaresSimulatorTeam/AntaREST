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

import { render, screen } from "@testing-library/react";
import { createMRTColumnHelper } from "material-react-table";
import { useState } from "react";
import { vi } from "vitest";
import GroupedDataTable from ".";

interface Row {
  name: string;
  value: number;
}

const columnHelper = createMRTColumnHelper<Row>();
const columns = [columnHelper.accessor("value", { header: "Value" })];

test("reflects updates coming from the `data` prop after mount (e.g. edited via an external drawer)", () => {
  const { rerender } = render(
    <GroupedDataTable data={[{ name: "Reserve A", value: 1 }]} columns={columns} />,
  );

  expect(screen.getByText("1")).toBeInTheDocument();

  rerender(<GroupedDataTable data={[{ name: "Reserve A", value: 2 }]} columns={columns} />);

  expect(screen.queryByText("1")).not.toBeInTheDocument();
  expect(screen.getByText("2")).toBeInTheDocument();
});

test("does not loop when `data` gets a new-but-equal reference on every render", () => {
  const onDataChange = vi.fn();

  // Reproduces the clusters views pattern that caused "Maximum update depth
  // exceeded": `data` is rebuilt on every render (e.g. a `data = []` fallback
  // while a fetch is pending) and `onDataChange` triggers a parent state
  // update, so any redundant `tableData` update re-renders in a loop.
  function Parent() {
    const [updateCount, setUpdateCount] = useState(0);

    return (
      <>
        <div data-testid="update-count">{updateCount}</div>
        <GroupedDataTable
          data={[{ name: "Reserve A", value: 42 }]}
          columns={columns}
          onDataChange={(data) => {
            onDataChange(data);
            setUpdateCount((prev) => prev + 1);
          }}
        />
      </>
    );
  }

  render(<Parent />);

  expect(screen.getByText("42")).toBeInTheDocument();
  expect(screen.getByTestId("update-count")).toHaveTextContent("1");
  expect(onDataChange).toHaveBeenCalledTimes(1);
});
