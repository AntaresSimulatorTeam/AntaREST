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

import Box from "@mui/material/Box";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SplitView from "@/components/common/SplitView";
import { mockGetBoundingClientRect } from "@/tests/mocks/mockGetBoundingClientRect";
import { mockHTMLCanvasElement } from "@/tests/mocks/mockHTMLCanvasElement";

import { Column } from "../../shared/constants";
import { EnhancedGridColumn } from "../../shared/types";

import MatrixGrid, { MatrixGridProps } from ".";

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
      <MatrixGrid
        data={data}
        rows={rows}
        columns={columns}
        width="100%"
        height="100%"
      />
    </Box>,
  );
};

const assertDimensions = (
  element: HTMLElement,
  expectedWidth: number,
  expectedHeight: number,
) => {
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
          <MatrixGrid
            data={DATA}
            rows={2}
            columns={COLUMNS}
            width="100%"
            height="100%"
          />
        </Box>,
      );

      matrix = getMatrixElement(container);
      assertDimensions(matrix, 300, 400);
    });
  });

  describe("portal management", () => {
    const renderSplitView = () => {
      return render(
        <Box style={{ width: "900px", height: "500px" }}>
          <SplitView id="test-split-view" sizes={[50, 50]}>
            {[0, 1].map((index) => (
              <Box key={index} sx={{ px: 2 }}>
                <MatrixGrid
                  data={DATA}
                  rows={2}
                  columns={COLUMNS}
                  width="100%"
                  height="100%"
                />
              </Box>
            ))}
          </SplitView>
        </Box>,
      );
    };

    const getPortal = () => document.getElementById("portal");

    test("should manage portal visibility on mount", () => {
      renderMatrixGrid();
      expect(getPortal()).toBeInTheDocument();
      expect(getPortal()?.style.display).toBe("none");
    });

    test("should toggle portal visibility on mouse events", async () => {
      const user = userEvent.setup();
      const { container } = renderMatrixGrid();
      const matrix = container.querySelector(".matrix-container");
      expect(matrix).toBeInTheDocument();

      await user.hover(matrix!);
      expect(getPortal()?.style.display).toBe("block");

      await user.unhover(matrix!);
      expect(getPortal()?.style.display).toBe("none");
    });

    test("should handle portal in split view", async () => {
      const user = userEvent.setup();
      renderSplitView();
      const matrices = document.querySelectorAll(".matrix-container");

      // Test portal behavior with multiple matrices
      await user.hover(matrices[0]);
      expect(getPortal()?.style.display).toBe("block");

      await user.hover(matrices[1]);
      expect(getPortal()?.style.display).toBe("block");

      await user.unhover(matrices[1]);
      expect(getPortal()?.style.display).toBe("none");
    });

    test("should maintain portal state when switching between matrices", async () => {
      const user = userEvent.setup();
      renderSplitView();
      const matrices = document.querySelectorAll(".matrix-container");

      for (const matrix of [matrices[0], matrices[1], matrices[0]]) {
        await user.hover(matrix);
        expect(getPortal()?.style.display).toBe("block");
      }

      await user.unhover(matrices[0]);
      expect(getPortal()?.style.display).toBe("none");
    });

    test("should handle unmounting correctly", () => {
      const { unmount } = renderSplitView();
      expect(getPortal()).toBeInTheDocument();

      unmount();
      expect(getPortal()).toBeInTheDocument();
      expect(getPortal()?.style.display).toBe("none");
    });
  });
});
