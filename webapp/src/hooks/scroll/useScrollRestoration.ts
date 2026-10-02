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

import { useCallback } from "react";
import { useScrollPersistence } from "./useScrollPersistence";

/**
 * Persists and restores the scroll position of a scrollable DOM element
 * via `sessionStorage` (rAF-throttled writes, Page Lifecycle flush).
 *
 * Attach the returned ref callback to any scrollable element:
 * ```tsx
 * const scrollRef = useScrollRestoration("my-list");
 * <div ref={scrollRef} style={{ overflow: "auto" }}>…</div>
 * ```
 *
 * The scroll listener is registered as `{ passive: true }`.
 *
 * @param key - Unique, stable key for this scrollable region. Pass `undefined` to disable.
 * @returns A ref callback to attach to a scrollable `HTMLElement`.
 */
export function useScrollRestoration(key: string | undefined): React.RefCallback<HTMLElement> {
  const persistence = useScrollPersistence(key);

  return useCallback<React.RefCallback<HTMLElement>>(
    (element) => {
      if (!element || !persistence) {
        return;
      }

      const { save, restore } = persistence;

      const scrollTop = restore();
      if (scrollTop !== null) {
        element.scrollTo({ top: scrollTop, behavior: "instant" });
      }

      const handleScroll = () => save(element.scrollTop);
      element.addEventListener("scroll", handleScroll, { passive: true });

      // Returning a function registers it as cleanup called when
      // the element is detached or the ref callback identity changes.
      return () => element.removeEventListener("scroll", handleScroll);
    },
    // Intentionally depend on `persistence`: a key change produces a new callback
    // identity, causing React to run the previous cleanup then re-invoke with
    // the element, triggering a fresh restore cycle.
    [persistence],
  );
}
