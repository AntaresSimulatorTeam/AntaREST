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

/**
 * Updated tests for MatrixActions after changes in the Matrix component.
 */
import type React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MatrixActions from ".";
import { MatrixProvider } from "../../context/MatrixContext";
import { vi } from "vitest";
import { UTCDate } from "@date-fns/utc";
import { TimeFrequency } from "@/components/common/Matrix/shared/constants";

vi.mock("../buttons/SplitButton", () => ({
  default: ({
    children,
    onClick,
    disabled,
  }: {
    children: React.ReactNode;
    onClick: () => void;
    disabled?: boolean;
  }) => (
    <button type="submit" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("../buttons/DownloadMatrixButton", () => ({
  default: ({ disabled, label }: { disabled: boolean; label?: string }) => (
    <button type="submit" disabled={disabled}>
      {label || "global.export"}
    </button>
  ),
}));

const defaultProps = {
  onImport: vi.fn(),
  onSave: vi.fn(),
  onMatrixUpdated: vi.fn(),
  studyId: "study1",
  path: "/path/to/matrix",
  disabled: false,
  isTimeSeries: true,
  canImport: true,
  dateTime: {
    values: [new UTCDate("2023-01-01"), new UTCDate("2023-01-02")],
    first_week_size: 0,
    level: TimeFrequency.Daily,
  },
};

type RenderOptions = Partial<typeof defaultProps>;
type ContextOverrides = Partial<{
  isSubmitting: boolean;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  isDirty: boolean;
}>;

const defaultContext = {
  currentState: { data: [[0]], aggregates: {} },
  isSubmitting: false,
  updateCount: 0,
  setMatrixData: vi.fn(),
  reset: vi.fn(),
  undo: vi.fn(),
  redo: vi.fn(),
  canUndo: true,
  canRedo: true,
  isDirty: false,
  aggregateTypes: [],
  filterPreview: {
    active: false,
    criteria: {
      columnsIndices: [],
      rowsIndices: [],
    },
  },
  setFilterPreview: vi.fn(),
};

const renderMatrixActions = (
  props: RenderOptions = {},
  contextOverrides: ContextOverrides = {},
) => {
  const contextValue = { ...defaultContext, ...contextOverrides };
  return render(
    <MatrixProvider {...contextValue}>
      <MatrixActions {...defaultProps} {...props} />
    </MatrixProvider>,
  );
};

const getButton = (label: string) => {
  const element = screen.queryByText(label) || screen.queryByRole("button", { name: label });
  const button = element?.closest("button");

  if (!button) {
    throw new Error(`Button with label "${label}" not found`);
  }

  return button;
};

const getActionButton = (label: string) => {
  const element = screen.getByLabelText(label);
  const button = element.querySelector("button");

  if (!button) {
    throw new Error(`Action button "${label}" not found`);
  }

  return button;
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MatrixActions", () => {
  describe("rendering", () => {
    test("renders all buttons and controls", () => {
      renderMatrixActions();

      expect(screen.getByLabelText("global.undo")).toBeInTheDocument();
      expect(screen.getByLabelText("global.redo")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "global.save" })).toBeInTheDocument();
      expect(screen.getByText("global.import")).toBeInTheDocument();
      expect(screen.getByText("global.export")).toBeInTheDocument();
    });
  });

  describe("undo/redo functionality", () => {
    test("manages undo button state correctly", () => {
      const { rerender } = renderMatrixActions({}, { canUndo: true });
      expect(getActionButton("global.undo")).not.toBeDisabled();

      rerender(
        <MatrixProvider {...{ ...defaultContext, canUndo: false }}>
          <MatrixActions {...defaultProps} />
        </MatrixProvider>,
      );
      expect(getActionButton("global.undo")).toBeDisabled();
    });

    test("manages redo button state correctly", () => {
      const { rerender } = renderMatrixActions({}, { canRedo: true });
      expect(getActionButton("global.redo")).not.toBeDisabled();

      rerender(
        <MatrixProvider {...{ ...defaultContext, canRedo: false }}>
          <MatrixActions {...defaultProps} />
        </MatrixProvider>,
      );
      expect(getActionButton("global.redo")).toBeDisabled();
    });

    test("handles undo/redo button clicks", async () => {
      const undoMock = vi.fn();
      const redoMock = vi.fn();
      renderMatrixActions({}, { undo: undoMock, redo: redoMock });

      const user = userEvent.setup();
      await user.click(getActionButton("global.undo"));
      expect(undoMock).toHaveBeenCalledTimes(1);

      await user.click(getActionButton("global.redo"));
      expect(redoMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("save functionality", () => {
    test("manages save button state based on update count", () => {
      const { rerender } = renderMatrixActions({}, { isDirty: false });
      expect(getButton("global.save")).toBeDisabled();

      rerender(
        <MatrixProvider {...{ ...defaultContext, isDirty: true }}>
          <MatrixActions {...defaultProps} />
        </MatrixProvider>,
      );
      expect(getButton("global.save")).not.toBeDisabled();
    });

    test("handles save button click", async () => {
      const user = userEvent.setup();
      renderMatrixActions({}, { isDirty: true });

      await user.click(getButton("global.save"));
      expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
    });

    test("disables save button during submission", () => {
      renderMatrixActions({}, { isSubmitting: true, isDirty: true });
      expect(getButton("global.save")).toBeDisabled();
    });
  });

  describe("import/export functionality", () => {
    test("handles import button click", async () => {
      const user = userEvent.setup();
      renderMatrixActions();

      await user.click(getButton("global.import"));
      expect(defaultProps.onImport).toHaveBeenCalledTimes(1);
    });

    test("manages button states during submission", () => {
      renderMatrixActions({}, { isSubmitting: true });
      expect(getButton("global.import")).toBeDisabled();
      expect(getButton("global.export")).toBeDisabled();
    });

    test("manages import button state based on canImport prop", () => {
      const { rerender } = renderMatrixActions();
      expect(getButton("global.import")).not.toBeDisabled();

      rerender(
        <MatrixProvider {...defaultContext}>
          <MatrixActions {...defaultProps} canImport={false} />
        </MatrixProvider>,
      );
      expect(getButton("global.import")).toBeDisabled();
    });

    test("manages export button state based on disabled prop", () => {
      const { rerender } = renderMatrixActions();
      expect(getButton("global.export")).not.toBeDisabled();

      rerender(
        <MatrixProvider {...defaultContext}>
          <MatrixActions {...defaultProps} disabled={true} />
        </MatrixProvider>,
      );
      expect(getButton("global.export")).toBeDisabled();
    });
  });
});
