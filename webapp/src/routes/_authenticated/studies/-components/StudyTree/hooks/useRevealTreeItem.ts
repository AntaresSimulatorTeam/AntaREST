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

import { finishStudyFolderReveal } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { treeItemClasses, useSimpleTreeViewApiRef } from "@mui/x-tree-view";
import { useEffect, useRef } from "react";

interface Options {
  requestId?: string;
  itemId: string | null;
  ready?: boolean;
}

/**
 * Reveals a tree row after loading and expansion, without scrolling the surrounding page.
 *
 * @param options - The pending reveal and its loading state.
 * @param options.requestId - Identifies a single reveal, including repeated visits.
 * @param options.itemId - Tree item to reveal, or null for the managed root.
 * @param options.ready - Whether the target path has loaded and expanded.
 * @returns Refs to attach to the tree view.
 */
export function useRevealTreeItem({ requestId, itemId, ready = true }: Options) {
  const dispatch = useAppDispatch();
  const treeRef = useRef<HTMLUListElement>(null);
  const apiRef = useSimpleTreeViewApiRef();

  useEffect(() => {
    const section = treeRef.current?.closest<HTMLElement>("[data-study-tree-scroll]");

    if (!requestId || !ready || !section) {
      return;
    }

    let pendingFrame: number | undefined;
    let cancelled = false;
    let waitingForLayout = false;

    const tryReveal = () => {
      pendingFrame = undefined;

      // Scrollbar setup adds this marker and restores scroll in one task.
      // Reading it on a later frame keeps restoration ahead of the reveal.
      const viewport = section.querySelector<HTMLElement>("[data-overlayscrollbars-viewport]");

      if (!viewport || viewport.clientHeight === 0) {
        return;
      }

      const transitions = getRunningLayoutTransitions(section);

      if (transitions.length > 0) {
        waitingForLayout = true;

        void Promise.allSettled(transitions.map((transition) => transition.finished)).then(() => {
          waitingForLayout = false;
          scheduleReveal();
        });

        return;
      }

      if (itemId === null) {
        viewport.scrollTo({ top: 0, behavior: "instant" });
      } else {
        const item = apiRef.current?.getItemDOMElement(itemId);
        const row = item?.querySelector<HTMLElement>(`:scope > .${treeItemClasses.content}`);

        // Callers validate the target. Its row may still mount after the data is ready.
        if (!row) {
          return;
        }

        const rowBounds = row.getBoundingClientRect();

        if (rowBounds.height === 0) {
          return;
        }

        centerRowIfOutsideViewport(viewport, rowBounds);
      }

      dispatch(finishStudyFolderReveal(requestId));
    };

    function scheduleReveal() {
      if (cancelled || pendingFrame !== undefined || waitingForLayout) {
        return;
      }

      pendingFrame = requestAnimationFrame(tryReveal);
    }

    const mutationObserver = new MutationObserver(scheduleReveal);
    mutationObserver.observe(section, {
      childList: true,
      subtree: true,
      attributeFilter: ["style", "data-overlayscrollbars-viewport"],
    });

    const resizeObserver = new ResizeObserver(scheduleReveal);
    resizeObserver.observe(section);
    scheduleReveal();

    return () => {
      cancelled = true;

      if (pendingFrame !== undefined) {
        cancelAnimationFrame(pendingFrame);
      }

      mutationObserver.disconnect();
      resizeObserver.disconnect();
    };
  }, [apiRef, dispatch, itemId, ready, requestId]);

  return { treeRef, apiRef };
}

function getRunningLayoutTransitions(section: HTMLElement): Animation[] {
  const grid = section.closest("[data-study-tree]");

  // Scroll-driven scrollbar animations can stay pending. Only expansion transitions block reveal.
  return (
    grid
      ?.getAnimations?.({ subtree: true })
      .filter(
        (animation) =>
          animation.playState === "running" &&
          "transitionProperty" in animation &&
          (animation.transitionProperty === "height" ||
            animation.transitionProperty === "grid-template-rows"),
      ) ?? []
  );
}

function centerRowIfOutsideViewport(viewport: HTMLElement, { top, bottom, height }: DOMRect) {
  const viewportBounds = viewport.getBoundingClientRect();
  const isVisible = top >= viewportBounds.top && bottom <= viewportBounds.bottom;

  if (isVisible) {
    return;
  }

  const rowCenter = top + height / 2;
  const viewportCenter = viewportBounds.top + viewportBounds.height / 2;

  viewport.scrollTo({
    top: viewport.scrollTop + rowCenter - viewportCenter,
    behavior: "instant",
  });
}
