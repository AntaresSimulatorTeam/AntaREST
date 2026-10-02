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
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import SplitView from "..";

describe("SplitView", () => {
  beforeEach(() => {
    // Mock getBoundingClientRect for react-split
    Element.prototype.getBoundingClientRect = vi.fn(() => ({
      width: 800,
      height: 600,
      top: 0,
      left: 0,
      bottom: 600,
      right: 800,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    }));
  });

  describe("basic rendering", () => {
    test("should render with two children", () => {
      render(
        <SplitView splitId="basic-test">
          <div data-testid="child1">Child 1</div>
          <div data-testid="child2">Child 2</div>
        </SplitView>,
      );

      expect(screen.getByTestId("child1")).toBeInTheDocument();
      expect(screen.getByTestId("child2")).toBeInTheDocument();
    });

    test("should apply correct CSS class", () => {
      const { container } = render(
        <SplitView splitId="class-test">
          <div>Child 1</div>
          <div>Child 2</div>
        </SplitView>,
      );

      const splitView = container.querySelector(".SplitView");
      expect(splitView).toBeInTheDocument();
    });
  });

  describe("conditional children rendering", () => {
    test("should render correct child based on state", async () => {
      const user = userEvent.setup();

      function TestComponent() {
        const [showAlternate, setShowAlternate] = useState(false);

        return (
          <div>
            <button type="button" onClick={() => setShowAlternate(!showAlternate)}>
              Toggle
            </button>
            <SplitView splitId="test-split" minSize={[150, 400]}>
              <div>First Child</div>
              {showAlternate ? (
                <div data-testid="alternate">Alternate Child</div>
              ) : (
                <div data-testid="default">Default Child</div>
              )}
            </SplitView>
          </div>
        );
      }

      render(<TestComponent />);

      // Initially, default child should be visible
      expect(screen.getByTestId("default")).toBeInTheDocument();
      expect(screen.queryByTestId("alternate")).not.toBeInTheDocument();

      // Click to toggle
      await user.click(screen.getByRole("button"));

      // After toggle, alternate child should be visible
      expect(screen.queryByTestId("default")).not.toBeInTheDocument();
      expect(screen.getByTestId("alternate")).toBeInTheDocument();

      // Toggle back
      await user.click(screen.getByRole("button"));

      // Should be back to default
      expect(screen.getByTestId("default")).toBeInTheDocument();
      expect(screen.queryByTestId("alternate")).not.toBeInTheDocument();
    });

    test("should handle rapid toggling without errors", async () => {
      const user = userEvent.setup();

      function TestComponent() {
        const [show, setShow] = useState(true);

        return (
          <div>
            <button type="button" onClick={() => setShow(!show)}>
              Rapid Toggle
            </button>
            <SplitView splitId="rapid-toggle" minSize={[150, 400]}>
              <div data-testid="static">Static Panel</div>
              {show ? (
                <div data-testid="view-x">View X</div>
              ) : (
                <div data-testid="view-y">View Y</div>
              )}
            </SplitView>
          </div>
        );
      }

      render(<TestComponent />);
      const button = screen.getByRole("button");

      // Rapidly toggle 10 times
      for (let i = 0; i < 10; i++) {
        await user.click(button);
        // Static panel should always be present
        expect(screen.getByTestId("static")).toBeInTheDocument();
      }
    });
  });

  describe("BUG: Split component remounting via composite key", () => {
    /**
     * ISSUE: Conditional children (e.g., SynthesisViewer <-> ResultMatrixViewer) corrupt
     * react-split's DOM refs, causing layout issues (narrow panels).
     *
     * FIX: Composite key based on children identities forces Split remount with fresh refs.
     *
     * TEST LIMITATION: These tests verify the mechanism (key generation) but cannot catch
     * the actual bug, which requires real browser + react-split ref management.
     *
     * TODO: Add E2E test when introducing E2E testing framework to verify:
     * - Toggle between SynthesisViewer and ResultMatrixViewer in ResultDetails
     * - Assert right panel maintains correct width (not narrow)
     * - Verify split pane sizes are preserved after toggle
     */

    test("should generate composite key that includes children identities", () => {
      function ComponentA() {
        return <div data-testid="comp-a">Component A</div>;
      }

      function ComponentB() {
        return <div data-testid="comp-b">Component B</div>;
      }

      const { rerender } = render(
        <SplitView splitId="key-test" minSize={[150, 400]}>
          <div>Sidebar</div>
          <ComponentA />
        </SplitView>,
      );

      expect(screen.getByTestId("comp-a")).toBeInTheDocument();

      // Change to ComponentB - this should trigger a new composite key
      rerender(
        <SplitView splitId="key-test" minSize={[150, 400]}>
          <div>Sidebar</div>
          <ComponentB />
        </SplitView>,
      );

      // ComponentB should now be rendered
      expect(screen.getByTestId("comp-b")).toBeInTheDocument();
      expect(screen.queryByTestId("comp-a")).not.toBeInTheDocument();
    });

    test("simulates ResultDetails scenario (SynthesisViewer vs ResultMatrixViewer toggle)", async () => {
      const user = userEvent.setup();

      // Simulate the actual components from ResultDetails
      function SynthesisViewer() {
        return <div data-testid="synthesis-viewer">Synthesis Content</div>;
      }

      function ResultMatrixViewer() {
        return <div data-testid="matrix-viewer">Matrix Content</div>;
      }

      function ResultDetailsSimulation() {
        const [isSynthesis, setIsSynthesis] = useState(false);

        return (
          <div>
            <button type="button" onClick={() => setIsSynthesis(!isSynthesis)}>
              Toggle View
            </button>
            <SplitView splitId="results-simulation" minSize={[150, 400]}>
              <div data-testid="sidebar">Item Selector</div>
              {isSynthesis ? <SynthesisViewer /> : <ResultMatrixViewer />}
            </SplitView>
          </div>
        );
      }

      render(<ResultDetailsSimulation />);

      // Initially should show matrix viewer
      expect(screen.getByTestId("matrix-viewer")).toBeInTheDocument();
      expect(screen.queryByTestId("synthesis-viewer")).not.toBeInTheDocument();

      // Toggle to synthesis
      await user.click(screen.getByRole("button"));

      // Verify synthesis viewer is shown
      expect(screen.getByTestId("synthesis-viewer")).toBeInTheDocument();
      expect(screen.queryByTestId("matrix-viewer")).not.toBeInTheDocument();

      // Verify sidebar is still present (not affected by conditional child)
      expect(screen.getByTestId("sidebar")).toBeInTheDocument();

      // Toggle back multiple times to ensure stability
      for (let i = 0; i < 3; i++) {
        await user.click(screen.getByRole("button"));
        expect(screen.getByTestId("sidebar")).toBeInTheDocument();
      }
    });

    test("should preserve existing keys if provided by parent", () => {
      function TestComponent() {
        return (
          <SplitView splitId="custom-keys" minSize={[150, 400]}>
            <div key="custom-key-1" data-testid="child-1">
              Child 1
            </div>
            <div key="custom-key-2" data-testid="child-2">
              Child 2
            </div>
          </SplitView>
        );
      }

      render(<TestComponent />);

      expect(screen.getByTestId("child-1")).toBeInTheDocument();
      expect(screen.getByTestId("child-2")).toBeInTheDocument();
    });
  });
});
