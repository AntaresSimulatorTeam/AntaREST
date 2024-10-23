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

import { act, render } from "@testing-library/react";
import MatrixGrid, { MatrixGridProps } from ".";
import Box from "@mui/material/Box";
import { mockGetBoundingClientRect } from "../../../tests/mocks/mockGetBoundingClientRect";
import { type EnhancedGridColumn, Column } from "./types";
import { mockHTMLCanvasElement } from "../../../tests/mocks/mockHTMLCanvasElement";
import SplitView from "../SplitView";

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

  describe("MatrixGrid rendering", () => {
    describe("MatrixGrid portal management", () => {
      test("should handle portal in split view", () => {
        const data = [
          [1, 2],
          [4, 5],
        ];

        const columns: EnhancedGridColumn[] = [
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

        const { container } = render(
          <Box style={{ width: "900px", height: "500px" }}>
            <SplitView id="test-split-view" sizes={[50, 50]}>
              <Box sx={{ px: 2 }}>
                <MatrixGrid
                  data={data}
                  rows={2}
                  columns={columns}
                  width="100%"
                  height="100%"
                />
              </Box>
              <Box sx={{ px: 2 }}>
                <MatrixGrid
                  data={data}
                  rows={2}
                  columns={columns}
                  width="100%"
                  height="100%"
                />
              </Box>
            </SplitView>
          </Box>,
        );

        const matrices = container.querySelectorAll(".matrix-container");

        matrices.forEach((matrix, index) => {
          console.log(`Matrix ${index} classes:`, matrix.className, matrix);
        });

        expect(matrices.length).toBe(2);

        if (matrices.length === 2) {
          act(() => {
            matrices[0].dispatchEvent(
              new Event("mouseenter", { bubbles: true }),
            );
          });

          act(() => {
            matrices[1].dispatchEvent(
              new Event("mouseenter", { bubbles: true }),
            );
          });

          act(() => {
            matrices[1].dispatchEvent(
              new Event("mouseleave", { bubbles: true }),
            );
          });
        }
      });
    });
  });
});
