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

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MatrixActions from "./MatrixActions";

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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all buttons and controls", () => {
    render(<MatrixActions {...defaultProps} />);

    expect(screen.getByLabelText("global.undo")).toBeDefined();
    expect(screen.getByLabelText("global.redo")).toBeDefined();
    expect(screen.getByText("(0)")).toBeDefined();
    expect(screen.getByText("global.import")).toBeDefined();
    expect(screen.getByText("global.export")).toBeDefined();
  });

  it("disables undo button when canUndo is false", () => {
    render(<MatrixActions {...defaultProps} canUndo={false} />);
    expect(
      screen.getByLabelText("global.undo").querySelector("button"),
    ).toBeDisabled();
  });

  it("disables redo button when canRedo is false", () => {
    render(<MatrixActions {...defaultProps} canRedo={false} />);
    expect(
      screen.getByLabelText("global.redo").querySelector("button"),
    ).toBeDisabled();
  });

  it("calls undo function when undo button is clicked", () => {
    render(<MatrixActions {...defaultProps} />);
    const undoButton = screen
      .getByLabelText("global.undo")
      .querySelector("button");
    if (undoButton) {
      fireEvent.click(undoButton);
      expect(defaultProps.undo).toHaveBeenCalled();
    } else {
      throw new Error("Undo button not found");
    }
  });

  it("calls redo function when redo button is clicked", () => {
    render(<MatrixActions {...defaultProps} />);
    const redoButton = screen
      .getByLabelText("global.redo")
      .querySelector("button");
    if (redoButton) {
      fireEvent.click(redoButton);
      expect(defaultProps.redo).toHaveBeenCalled();
    } else {
      throw new Error("Redo button not found");
    }
  });

  it("disables save button when pendingUpdatesCount is 0", () => {
    render(<MatrixActions {...defaultProps} />);
    expect(screen.getByText("(0)").closest("button")).toBeDisabled();
  });

  it("enables save button when pendingUpdatesCount is greater than 0", () => {
    render(<MatrixActions {...defaultProps} pendingUpdatesCount={1} />);
    expect(screen.getByText("(1)").closest("button")).not.toBeDisabled();
  });

  it("calls onSave function when save button is clicked", () => {
    render(<MatrixActions {...defaultProps} pendingUpdatesCount={1} />);
    const saveButton = screen.getByText("(1)").closest("button");
    if (saveButton) {
      fireEvent.click(saveButton);
      expect(defaultProps.onSave).toHaveBeenCalled();
    } else {
      throw new Error("Save button not found");
    }
  });

  it("shows loading state on save button when isSubmitting is true", () => {
    render(
      <MatrixActions
        {...defaultProps}
        isSubmitting={true}
        pendingUpdatesCount={1}
      />,
    );
    expect(screen.getByText("(1)").closest("button")).toBeDisabled();
  });

  it("calls onImport function when import button is clicked", () => {
    render(<MatrixActions {...defaultProps} />);
    fireEvent.click(screen.getByText("global.import"));
    expect(defaultProps.onImport).toHaveBeenCalled();
  });

  it("disables import button when isSubmitting is true", () => {
    render(<MatrixActions {...defaultProps} isSubmitting={true} />);
    expect(screen.getByText("global.import")).toBeDisabled();
  });

  it("passes correct props to DownloadMatrixButton", () => {
    const { rerender } = render(<MatrixActions {...defaultProps} />);
    expect(screen.getByText("global.export")).not.toBeDisabled();

    rerender(<MatrixActions {...defaultProps} disabled={true} />);
    expect(screen.getByText("global.export")).toBeDisabled();

    rerender(<MatrixActions {...defaultProps} isSubmitting={true} />);
    expect(screen.getByText("global.export")).toBeDisabled();
  });
});
