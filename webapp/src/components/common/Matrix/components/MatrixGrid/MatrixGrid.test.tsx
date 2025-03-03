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

import { render } from "@testing-library/react";
import { Box } from "@mui/material";
import MatrixGrid, { type MatrixGridProps } from ".";
import type { EnhancedGridColumn } from "../../shared/types";
import { mockGetBoundingClientRect } from "../../../../../tests/mocks/mockGetBoundingClientRect";
import { mockHTMLCanvasElement } from "../../../../../tests/mocks/mockHTMLCanvasElement";
import { Column } from "../../shared/constants";

interface RenderMatrixOptions {
  width?: string;
  height?: string;
  data?: MatrixGridProps["data"];
  columns?: EnhancedGridColumn[];
  rows?: number;
}

const setupMocks = () => {
  mockHTMLCanvasElement();
  mockGetBoundingClientRect();
  vi.clearAllMocks();
};

const COLUMNS: EnhancedGridColumn[] = [
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

const DATA = [
  [1, 2, 3],
  [4, 5, 6],
];

const renderMatrixGrid = ({
  width = "450px",
  height = "500px",
  data = DATA,
  columns = COLUMNS,
  rows = 2,
}: RenderMatrixOptions = {}) => {
  return render(
    <Box style={{ width, height }}>
      <MatrixGrid data={data} rows={rows} columns={columns} width="100%" height="100%" />
    </Box>,
  );
};

const assertDimensions = (element: HTMLElement, expectedWidth: number, expectedHeight: number) => {
  const rect = element.getBoundingClientRect();
  expect(rect.width).toBe(expectedWidth);
  expect(rect.height).toBe(expectedHeight);
};

const getMatrixElement = (container: HTMLElement) => {
  const matrix = container.firstChild;

  if (!(matrix instanceof HTMLElement)) {
    throw new Error("Expected an HTMLElement but received a different node.");
  }

  return matrix;
};

describe("MatrixGrid", () => {
  beforeEach(setupMocks);

  describe("rendering", () => {
    test("should match container dimensions", () => {
      const { container } = renderMatrixGrid();
      const matrix = getMatrixElement(container);

      expect(matrix).toBeInTheDocument();
      assertDimensions(matrix, 450, 500);
    });

    test("should render with empty data", () => {
      const { container } = renderMatrixGrid({ data: [], rows: 0 });
      const matrix = getMatrixElement(container);

      expect(matrix).toBeInTheDocument();
      assertDimensions(matrix, 450, 500);
    });

    test("should update dimensions when resized", () => {
      const { container, rerender } = renderMatrixGrid();
      let matrix = getMatrixElement(container);
      assertDimensions(matrix, 450, 500);

      rerender(
        <Box style={{ width: "300px", height: "400px" }}>
          <MatrixGrid data={DATA} rows={2} columns={COLUMNS} width="100%" height="100%" />
        </Box>,
      );

      matrix = getMatrixElement(container);
      assertDimensions(matrix, 300, 400);
    });
  });
});
