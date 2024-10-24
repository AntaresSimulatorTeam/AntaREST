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

import { render } from "@testing-library/react";
import MatrixGrid, { MatrixGridProps } from ".";
import Box from "@mui/material/Box";
import { mockGetBoundingClientRect } from "../../../tests/mocks/mockGetBoundingClientRect";
import { type EnhancedGridColumn, Column } from "./types";
import { mockHTMLCanvasElement } from "../../../tests/mocks/mockHTMLCanvasElement";
import SplitView from "../SplitView";
import userEvent from "@testing-library/user-event";

beforeEach(() => {
  mockHTMLCanvasElement();
  mockGetBoundingClientRect();
  vi.clearAllMocks();
});

function renderMatrixGrid(
  width: string,
  height: string,
  data: MatrixGridProps["data"],
  columns: EnhancedGridColumn[],
  rows: number,
) {
  return render(
    <Box style={{ width, height }}>
      <MatrixGrid
        data={data}
        rows={rows}
        columns={columns}
        width="100%"
        height="100%"
      />
    </Box>,
  );
}

function assertDimensions(
  element: HTMLElement,
  expectedWidth: number,
  expectedHeight: number,
) {
  const rect = element.getBoundingClientRect();
  expect(rect.width).toBe(expectedWidth);
  expect(rect.height).toBe(expectedHeight);
}

describe("MatrixGrid rendering", () => {
  test("MatrixGrid should be rendered within a 450x500px container and match these dimensions", () => {
    const data = [
      [1, 2, 3],
      [4, 5, 6],
    ];

    const columns = [
      {
        id: "col1",
        title: "Column 1",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col2",
        title: "Column 2",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col3",
        title: "Column 3",
        width: 100,
        type: Column.Number,
        editable: true,
      },
    ];

    const rows = 2;

    // Render the MatrixGrid inside a parent container with specific dimensions
    const { container } = renderMatrixGrid(
      "450px", // Use inline style for exact measurement
      "500px",
      data,
      columns,
      rows,
    );

    const matrix = container.firstChild;

    if (matrix instanceof HTMLElement) {
      expect(matrix).toBeInTheDocument();
      assertDimensions(matrix, 450, 500);
    } else {
      throw new Error("Expected an HTMLElement but received a different node.");
    }
  });

  test("MatrixGrid should render correctly with no data", () => {
    const data: MatrixGridProps["data"] = [];

    const columns = [
      {
        id: "col1",
        title: "Column 1",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col2",
        title: "Column 2",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col3",
        title: "Column 3",
        width: 100,
        type: Column.Number,
        editable: true,
      },
    ];

    const rows = 0;

    const { container } = renderMatrixGrid(
      "450px",
      "500px",
      data,
      columns,
      rows,
    );

    const matrix = container.firstChild;

    if (matrix instanceof HTMLElement) {
      expect(matrix).toBeInTheDocument();
      assertDimensions(matrix, 450, 500);
    } else {
      throw new Error("Expected an HTMLElement but received a different node.");
    }
  });

  test("MatrixGrid should match the provided dimensions when resized", () => {
    const data = [
      [1, 2, 3],
      [4, 5, 6],
    ];

    const columns = [
      {
        id: "col1",
        title: "Column 1",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col2",
        title: "Column 2",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col3",
        title: "Column 3",
        width: 100,
        type: Column.Number,
        editable: true,
      },
    ];

    const rows = 2;

    const { container, rerender } = renderMatrixGrid(
      "450px",
      "500px",
      data,
      columns,
      rows,
    );

    let matrix = container.firstChild;

    if (matrix instanceof HTMLElement) {
      assertDimensions(matrix, 450, 500);
    } else {
      throw new Error("Expected an HTMLElement but received a different node.");
    }

    rerender(
      <Box style={{ width: "300px", height: "400px" }}>
        <MatrixGrid
          data={data}
          rows={rows}
          columns={columns}
          width="100%"
          height="100%"
        />
      </Box>,
    );

    matrix = container.firstChild;

    if (matrix instanceof HTMLElement) {
      assertDimensions(matrix, 300, 400);
    } else {
      throw new Error("Expected an HTMLElement but received a different node.");
    }
  });

  describe("MatrixGrid portal management", () => {
    const sampleData = [
      [1, 2],
      [4, 5],
    ];

    const sampleColumns: EnhancedGridColumn[] = [
      {
        id: "col1",
        title: "Column 1",
        width: 100,
        type: Column.Number,
        editable: true,
      },
      {
        id: "col2",
        title: "Column 2",
        width: 100,
        type: Column.Number,
        editable: true,
      },
    ];

    test("should create portal when MatrixGrid mounts", () => {
      render(
        <MatrixGrid
          data={sampleData}
          rows={2}
          columns={sampleColumns}
          width="100%"
          height="100%"
        />,
      );

      const portal = document.getElementById("portal");
      expect(portal).toBeInTheDocument();
      expect(portal?.style.display).toBe("none");
    });

    test("should show/hide portal on mouse enter/leave", async () => {
      const user = userEvent.setup();
      const { container } = render(
        <MatrixGrid
          data={sampleData}
          rows={2}
          columns={sampleColumns}
          width="100%"
          height="100%"
        />,
      );

      const matrix = container.querySelector(".matrix-container");
      expect(matrix).toBeInTheDocument();

      // Mouse enter
      await user.hover(matrix!);
      const portalAfterEnter = document.getElementById("portal");
      expect(portalAfterEnter?.style.display).toBe("block");

      // Mouse leave
      await user.unhover(matrix!);
      const portalAfterLeave = document.getElementById("portal");
      expect(portalAfterLeave?.style.display).toBe("none");
    });

    test("should handle portal in split view with multiple matrices", async () => {
      const user = userEvent.setup();

      render(
        <Box style={{ width: "900px", height: "500px" }}>
          <SplitView id="test-split-view" sizes={[50, 50]}>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
          </SplitView>
        </Box>,
      );

      const matrices = document.querySelectorAll(".matrix-container");
      expect(matrices.length).toBe(2);

      // Test first matrix
      await user.hover(matrices[0]);
      expect(document.getElementById("portal")?.style.display).toBe("block");

      // Test second matrix while first is still hovered
      await user.hover(matrices[1]);
      expect(document.getElementById("portal")?.style.display).toBe("block");

      // Leave second matrix
      await user.unhover(matrices[1]);
      const portalAfterSecondLeave = document.getElementById("portal");
      expect(portalAfterSecondLeave?.style.display).toBe("none");
    });

    test("should maintain portal when switching between matrices", async () => {
      const user = userEvent.setup();

      render(
        <Box style={{ width: "900px", height: "500px" }}>
          <SplitView id="test-split-view" sizes={[50, 50]}>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
          </SplitView>
        </Box>,
      );

      const matrices = document.querySelectorAll(".matrix-container");

      // Rapid switching between matrices
      await user.hover(matrices[0]);
      expect(document.getElementById("portal")?.style.display).toBe("block");

      await user.hover(matrices[1]);
      expect(document.getElementById("portal")?.style.display).toBe("block");

      await user.hover(matrices[0]);
      expect(document.getElementById("portal")?.style.display).toBe("block");

      // Final cleanup
      await user.unhover(matrices[0]);
      expect(document.getElementById("portal")?.style.display).toBe("none");
    });

    test("should handle unmounting matrices in split view", () => {
      const { unmount } = render(
        <Box style={{ width: "900px", height: "500px" }}>
          <SplitView id="test-split-view" sizes={[50, 50]}>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
            <Box sx={{ px: 2 }}>
              <MatrixGrid
                data={sampleData}
                rows={2}
                columns={sampleColumns}
                width="100%"
                height="100%"
              />
            </Box>
          </SplitView>
        </Box>,
      );

      const portal = document.getElementById("portal");
      expect(portal).toBeInTheDocument();

      unmount();
      expect(document.getElementById("portal")).toBeInTheDocument();
      expect(document.getElementById("portal")?.style.display).toBe("none");
    });
  });
});
