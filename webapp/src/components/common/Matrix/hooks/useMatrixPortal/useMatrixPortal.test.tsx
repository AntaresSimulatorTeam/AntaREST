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

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useMatrixPortal } from "../useMatrixPortal";

function NonRefComponent() {
  return <div data-testid="non-ref-container">Test Container</div>;
}

function TestComponent() {
  const { containerRef, handleMouseEnter, handleMouseLeave } =
    useMatrixPortal();
  return (
    <div
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      data-testid="ref-container"
    >
      Test Container
    </div>
  );
}

describe("useMatrixPortal", () => {
  beforeEach(() => {
    cleanup();
    const existingPortal = document.getElementById("portal");
    if (existingPortal) {
      existingPortal.remove();
    }
  });

  test("should create hidden portal initially", () => {
    render(<TestComponent />);
    const portal = document.getElementById("portal");
    expect(portal).toBeInTheDocument();
    expect(portal?.style.display).toBe("none");
  });

  test("should show portal with correct styles when mouse enters", async () => {
    const user = userEvent.setup();
    render(<TestComponent />);

    const container = screen.getByTestId("ref-container");
    await user.hover(container);

    const portal = document.getElementById("portal");
    expect(portal).toBeInTheDocument();
    expect(portal?.style.display).toBe("block");
    expect(portal?.style.position).toBe("fixed");
    expect(portal?.style.left).toBe("0px");
    expect(portal?.style.top).toBe("0px");
    expect(portal?.style.zIndex).toBe("9999");
  });

  test("should hide portal when mouse leaves", async () => {
    const user = userEvent.setup();
    render(<TestComponent />);

    const container = screen.getByTestId("ref-container");

    // Show portal
    await user.hover(container);
    expect(document.getElementById("portal")?.style.display).toBe("block");

    // Hide portal
    await user.unhover(container);
    expect(document.getElementById("portal")?.style.display).toBe("none");
  });

  test("should keep portal hidden if containerRef is null", async () => {
    const user = userEvent.setup();

    // First render test component to create portal
    render(<TestComponent />);
    const portal = document.getElementById("portal");
    expect(portal?.style.display).toBe("none");

    cleanup(); // Clean up the test component

    // Then render component without ref
    render(<NonRefComponent />);
    const container = screen.getByTestId("non-ref-container");
    await user.hover(container);

    // Portal should stay hidden
    expect(portal?.style.display).toBe("none");
  });

  test("should handle multiple mouse enter/leave cycles", async () => {
    const user = userEvent.setup();
    render(<TestComponent />);

    const container = screen.getByTestId("ref-container");
    const portal = document.getElementById("portal");

    // First cycle
    await user.hover(container);
    expect(portal?.style.display).toBe("block");

    await user.unhover(container);
    expect(portal?.style.display).toBe("none");

    // Second cycle
    await user.hover(container);
    expect(portal?.style.display).toBe("block");

    await user.unhover(container);
    expect(portal?.style.display).toBe("none");
  });

  test("should handle rapid mouse events", async () => {
    const user = userEvent.setup();
    render(<TestComponent />);

    const container = screen.getByTestId("ref-container");
    const portal = document.getElementById("portal");

    // Rapid sequence
    await user.hover(container);
    await user.unhover(container);
    await user.hover(container);

    expect(portal?.style.display).toBe("block");
  });

  test("should maintain portal existence across multiple component instances", () => {
    // Render first instance
    const { unmount } = render(<TestComponent />);
    expect(document.getElementById("portal")).toBeInTheDocument();

    // Unmount first instance
    unmount();

    // Render second instance
    render(<TestComponent />);
    expect(document.getElementById("portal")).toBeInTheDocument();
  });
});
