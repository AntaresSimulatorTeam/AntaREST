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

import { deferred } from "@/tests/queryUtils";
import { SimpleTreeView, TreeItem } from "@mui/x-tree-view";
import { act, render, screen, waitFor } from "@testing-library/react";
import { finishStudyFolderReveal } from "@/redux/ducks/studies";
import { useRevealTreeItem } from "../useRevealTreeItem";

const { dispatch } = vi.hoisted(() => ({ dispatch: vi.fn() }));
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => dispatch }));
vi.mock("@/redux/store", () => ({ default: {} }));

let rowTop = 250;
let rowHeight = 20;
const scrollTo = vi.fn();
const originalScrollTo = HTMLElement.prototype.scrollTo;

function Harness({
  requestId = "request-1",
  ready = true,
  showItem = true,
  itemId = "target",
  initialized = true,
}: {
  requestId?: string;
  ready?: boolean;
  showItem?: boolean;
  itemId?: string | null;
  initialized?: boolean;
}) {
  const { treeRef, apiRef } = useRevealTreeItem({ requestId, ready, itemId });

  return (
    <div data-study-tree data-testid="grid">
      <div data-study-tree-scroll>
        <div data-overlayscrollbars-viewport={initialized ? "" : undefined} data-testid="viewport">
          <SimpleTreeView ref={treeRef} apiRef={apiRef} selectedItems={itemId}>
            {showItem && <TreeItem itemId="target" label="Target folder" />}
          </SimpleTreeView>
        </div>
      </div>
    </div>
  );
}

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    vi.fn(() => ({ observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() })),
  );
  dispatch.mockClear();
  scrollTo.mockClear();
  rowTop = 250;
  rowHeight = 20;
  HTMLElement.prototype.scrollTo = scrollTo;
  vi.spyOn(Element.prototype, "clientHeight", "get").mockReturnValue(100);
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const top = this.classList.contains("MuiTreeItem-content") ? rowTop : 0;
    const height = this.classList.contains("MuiTreeItem-content") ? rowHeight : 100;

    return new DOMRect(0, top, 100, height);
  });
});

afterEach(() => {
  HTMLElement.prototype.scrollTo = originalScrollTo;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test.each([
  { position: "below", top: 250, scrollTop: 0, expected: 210 },
  { position: "above", top: -30, scrollTop: 200, expected: 130 },
])(
  "centers a row $position the viewport by scrolling only the explorer",
  async ({ top, scrollTop, expected }) => {
    rowTop = top;
    const { rerender } = render(<Harness ready={false} />);
    const viewport = screen.getByTestId("viewport");
    viewport.scrollTop = scrollTop;

    rerender(<Harness />);

    await waitFor(() =>
      expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1")),
    );
    expect(scrollTo).toHaveBeenCalledTimes(1);
    expect(scrollTo).toHaveBeenCalledWith({ top: expected, behavior: "instant" });
    expect(scrollTo.mock.contexts[0]).toBe(viewport);

    rerender(<Harness requestId="request-2" />);

    await waitFor(() => expect(scrollTo).toHaveBeenCalledTimes(2));
    expect(dispatch).toHaveBeenLastCalledWith(finishStudyFolderReveal("request-2"));
  },
);

test("does not scroll when the folder is already visible", async () => {
  rowTop = 40;

  render(<Harness />);

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1")));
  expect(scrollTo).not.toHaveBeenCalled();
});

test("waits for loading and for the target to be mounted", async () => {
  const { rerender } = render(<Harness ready={false} />);
  await act(() => new Promise(requestAnimationFrame));

  expect(dispatch).not.toHaveBeenCalled();

  rerender(<Harness showItem={false} />);
  await act(() => new Promise(requestAnimationFrame));

  expect(dispatch).not.toHaveBeenCalled();

  rerender(<Harness />);

  await waitFor(() => expect(scrollTo).toHaveBeenCalledOnce());
  expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1"));
});

test("reveals after deferred viewport initialization and its synchronous scroll restoration", async () => {
  render(<Harness initialized={false} />);
  await act(() => new Promise(requestAnimationFrame));

  expect(scrollTo).not.toHaveBeenCalled();
  expect(dispatch).not.toHaveBeenCalled();

  const viewport = screen.getByTestId("viewport");

  act(() => {
    // OverlayScrollbars adds this attribute and restores scroll in the same task.
    viewport.setAttribute("data-overlayscrollbars-viewport", "");
    viewport.scrollTop = 80;
  });

  await waitFor(() => expect(scrollTo).toHaveBeenCalledOnce());
  expect(scrollTo).toHaveBeenCalledWith({ top: 290, behavior: "instant" });
  expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1"));
});

test("retries a zero-height row when its expansion styles change", async () => {
  rowHeight = 0;

  render(<Harness />);
  await act(() => new Promise(requestAnimationFrame));

  expect(dispatch).not.toHaveBeenCalled();

  act(() => {
    rowHeight = 20;
    screen.getByText("Target folder").style.height = "20px";
  });

  await waitFor(() => expect(scrollTo).toHaveBeenCalledOnce());
  expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1"));
});

test("only finishes the latest request when an earlier reveal is waiting for expansion", async () => {
  const animation = deferred<void>();
  let running = true;
  const { rerender } = render(<Harness ready={false} />);
  const getAnimations = vi.fn(() =>
    running
      ? [{ playState: "running", transitionProperty: "height", finished: animation.promise }]
      : [],
  );
  Object.defineProperty(screen.getByTestId("grid"), "getAnimations", { value: getAnimations });

  rerender(<Harness />);
  await waitFor(() => expect(getAnimations).toHaveBeenCalled());

  expect(scrollTo).not.toHaveBeenCalled();
  expect(dispatch).not.toHaveBeenCalled();

  getAnimations.mockClear();
  rerender(<Harness requestId="request-2" />);
  await waitFor(() => expect(getAnimations).toHaveBeenCalled());

  await act(async () => {
    running = false;
    animation.resolve();
    await animation.promise;
  });

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-2")));
  expect(dispatch).toHaveBeenCalledOnce();
  expect(scrollTo).toHaveBeenCalledOnce();
});

test("reveals the managed root by returning its section to the top", async () => {
  render(<Harness itemId={null} showItem={false} />);

  await waitFor(() => expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "instant" }));
  expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1"));
});

test("does not wait for scroll-driven scrollbar animations", async () => {
  const { rerender } = render(<Harness ready={false} />);
  Object.defineProperty(screen.getByTestId("grid"), "getAnimations", {
    value: () => [{ playState: "running", finished: new Promise(() => undefined) }],
  });

  rerender(<Harness />);

  await waitFor(() => expect(scrollTo).toHaveBeenCalledOnce());
  expect(dispatch).toHaveBeenCalledWith(finishStudyFolderReveal("request-1"));
});
