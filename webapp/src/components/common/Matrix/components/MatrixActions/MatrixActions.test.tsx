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

import type React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MatrixActions from ".";

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
    <button onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("../buttons/DownloadMatrixButton", () => ({
  default: ({ disabled, label }: { disabled: boolean; label?: string }) => (
    <button disabled={disabled}>{label || "global.export"}</button>
  ),
}));

describe("MatrixActions", () => {
  const defaultProps = {
    onImport: vi.fn(),
    onSave: vi.fn(),
    studyId: "study1",
    path: "/path/to/matrix",
    disabled: false,
    pendingUpdatesCount: 0,
    isSubmitting: false,
    undo: vi.fn(),
    redo: vi.fn(),
    canUndo: true,
    canRedo: true,
  };

  type RenderOptions = Partial<typeof defaultProps>;

  const renderMatrixActions = (props: RenderOptions = {}) => {
    return render(<MatrixActions {...defaultProps} {...props} />);
  };

  const getButton = (label: string) => {
    const element = screen.getByText(label);
    const button = element.closest("button");

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

  describe("rendering", () => {
    test("renders all buttons and controls", () => {
      renderMatrixActions();

      expect(screen.getByLabelText("global.undo")).toBeInTheDocument();
      expect(screen.getByLabelText("global.redo")).toBeInTheDocument();
      expect(screen.getByText("(0)")).toBeInTheDocument();
      expect(screen.getByText("global.import")).toBeInTheDocument();
      expect(screen.getByText("global.export")).toBeInTheDocument();
    });
  });

  describe("undo/redo functionality", () => {
    test("manages undo button state correctly", () => {
      const { rerender } = renderMatrixActions();
      expect(getActionButton("global.undo")).not.toBeDisabled();

      rerender(<MatrixActions {...defaultProps} canUndo={false} />);
      expect(getActionButton("global.undo")).toBeDisabled();
    });

    test("manages redo button state correctly", () => {
      const { rerender } = renderMatrixActions();
      expect(getActionButton("global.redo")).not.toBeDisabled();

      rerender(<MatrixActions {...defaultProps} canRedo={false} />);
      expect(getActionButton("global.redo")).toBeDisabled();
    });

    test("handles undo/redo button clicks", async () => {
      const user = userEvent.setup();
      renderMatrixActions();

      await user.click(getActionButton("global.undo"));
      expect(defaultProps.undo).toHaveBeenCalledTimes(1);

      await user.click(getActionButton("global.redo"));
      expect(defaultProps.redo).toHaveBeenCalledTimes(1);
    });
  });

  describe("save functionality", () => {
    test("manages save button state based on pending updates", () => {
      const { rerender } = renderMatrixActions();
      expect(getButton("(0)")).toBeDisabled();

      rerender(<MatrixActions {...defaultProps} pendingUpdatesCount={1} />);
      expect(getButton("(1)")).not.toBeDisabled();
    });

    test("handles save button click", async () => {
      const user = userEvent.setup();
      renderMatrixActions({ pendingUpdatesCount: 1 });

      await user.click(getButton("(1)"));
      expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
    });

    test("disables save button during submission", () => {
      renderMatrixActions({
        isSubmitting: true,
        pendingUpdatesCount: 1,
      });
      expect(getButton("(1)")).toBeDisabled();
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
      renderMatrixActions({ isSubmitting: true });

      expect(getButton("global.import")).toBeDisabled();
      expect(getButton("global.export")).toBeDisabled();
    });

    test("manages export button state based on disabled prop", () => {
      const { rerender } = renderMatrixActions();
      expect(getButton("global.export")).not.toBeDisabled();

      rerender(<MatrixActions {...defaultProps} disabled={true} />);
      expect(getButton("global.export")).toBeDisabled();
    });
  });
});
