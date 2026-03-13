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

import type { EventListeners } from "overlayscrollbars";
import { useEffect, useMemo, useRef } from "react";

/**
 * Persists and restores the scroll position of an OverlayScrollbars container
 * across page navigations and full page reloads using `sessionStorage`.
 *
 * **Optimisations over a naïve implementation:**
 *
 * - **`requestAnimationFrame`-throttled writes** – the raw `scroll` event can
 *   fire dozens of times per frame; we capture the latest `scrollTop` in a ref
 *   (essentially free) and flush it to `sessionStorage` at most once per frame.
 *
 * - **Page Lifecycle flush** – pending scroll positions are flushed when the
 *   document becomes `hidden` (`visibilitychange`) *and* on `beforeunload`,
 *   covering both mobile tab-switches and desktop full-page reloads.
 *
 * - **Automatic cleanup** – the rAF is cancelled and any pending value is
 *   flushed synchronously when the key changes or the component unmounts.
 *
 * - **Restored-value validation** – the stored value is guarded with
 *   `Number.isFinite` to prevent `NaN` / `Infinity` from corrupting the DOM.
 *
 * Usage: pass the returned `EventListeners` to `CustomScrollbar`'s `events` prop.
 *
 * @param key - A unique, stable identifier for this scrollable region.
 *   Pass `undefined` to disable persistence entirely.
 * @returns OverlayScrollbars `EventListeners` to spread onto `CustomScrollbar`,
 *   or `undefined` when `key` is not provided.
 */
export function useScrollRestoration(key: string | undefined): EventListeners | undefined {
  // Mutable state that lives across renders without triggering them.
  const rafId = useRef(0);
  const pending = useRef<number | null>(null);
  // Keep a ref-copy of the derived storage key so lifecycle callbacks
  // (which capture via closure at effect-setup time) always read the
  // latest value without needing to re-subscribe on every render.
  const storageKeyRef = useRef<string | null>(null);

  const storageKey = key ? `scroll-restore:${key}` : null;
  storageKeyRef.current = storageKey;

  // Lifecycle: flush & cleanup
  useEffect(() => {
    if (!storageKey) {
      return;
    }

    // Synchronously write the pending value to sessionStorage.
    const flush = () => {
      const sk = storageKeyRef.current;
      if (sk !== null && pending.current !== null) {
        sessionStorage.setItem(sk, String(pending.current));
        pending.current = null;
      }
    };

    // `visibilitychange` → `"hidden"` is the most reliable save-point
    // on modern browsers, including mobile (where `beforeunload` may
    // never fire).  See https://developer.chrome.com/blog/page-lifecycle-api
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        flush();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    // `beforeunload` is a fallback for older desktop browsers.
    window.addEventListener("beforeunload", flush);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("beforeunload", flush);
      cancelAnimationFrame(rafId.current);
      flush(); // ensure the last position is persisted on unmount / key change
    };
  }, [storageKey]);

  // OverlayScrollbars event listeners
  return useMemo<EventListeners | undefined>(() => {
    if (!storageKey) {
      return undefined;
    }

    return {
      initialized(instance) {
        const raw = sessionStorage.getItem(storageKey);

        if (raw !== null) {
          const scrollTop = Number(raw);

          if (Number.isFinite(scrollTop)) {
            instance
              .elements()
              .scrollOffsetElement.scrollTo({ top: scrollTop, behavior: "instant" });
          }
        }
      },

      scroll(instance) {
        // Capture is cheap – just a number assignment into a ref.
        pending.current = instance.elements().scrollOffsetElement.scrollTop;

        // Coalesce writes: cancel any previously-scheduled frame and
        // request a new one so we write at most once per rAF tick.
        cancelAnimationFrame(rafId.current);
        rafId.current = requestAnimationFrame(() => {
          const sk = storageKeyRef.current;

          if (sk !== null && pending.current !== null) {
            sessionStorage.setItem(sk, String(pending.current));
            pending.current = null;
          }
        });
      },
    };
  }, [storageKey]);
}
