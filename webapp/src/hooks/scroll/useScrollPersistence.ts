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

import { useCallback, useEffect, useRef } from "react";

interface ScrollPersistence {
  /** Enqueue a scroll position for `rAF`-throttled write to `sessionStorage`. */
  save: (scrollTop: number) => void;
  /** Return the persisted scroll position, or `null` if absent / invalid. */
  restore: () => number | null;
}

/**
 * Low-level persistence engine shared by all scroll-restoration hooks.
 *
 * Writes are `rAF`-throttled and flushed synchronously on
 * `visibilitychange → "hidden"`, `beforeunload`, and unmount / key change.
 *
 * @param key - Unique identifier for the scrollable region.
 *   Pass `undefined` to disable persistence entirely.
 * @returns A `ScrollPersistence` handle, or `null` when `key` is not provided.
 */
export function useScrollPersistence(key: string | undefined): ScrollPersistence | null {
  const animationFrameId = useRef<number | null>(null);
  const pendingScrollTop = useRef<number | null>(null);
  const storageKeyRef = useRef<string | null>(null);

  const storageKey = key ? `scroll-restore:${key}` : null;
  storageKeyRef.current = storageKey;

  useEffect(() => {
    if (!storageKey) {
      return;
    }

    // Capture storageKey so cleanup always flushes to the key that was active
    // when this effect ran, even if the key has since changed.
    const flush = () => {
      if (pendingScrollTop.current !== null) {
        sessionStorage.setItem(storageKey, String(pendingScrollTop.current));
        pendingScrollTop.current = null;
      }
    };

    // visibilitychange → "hidden" is the most reliable save-point on modern
    // browsers. See https://developer.chrome.com/blog/page-lifecycle-api
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        flush();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("beforeunload", flush); // fallback for older browsers

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("beforeunload", flush);

      if (animationFrameId.current !== null) {
        cancelAnimationFrame(animationFrameId.current);
      }

      flush(); // persist the last position on unmount / key change
    };
  }, [storageKey]);

  const save = useCallback((scrollTop: number) => {
    pendingScrollTop.current = scrollTop;

    if (animationFrameId.current !== null) {
      cancelAnimationFrame(animationFrameId.current);
    }

    animationFrameId.current = requestAnimationFrame(() => {
      const currentStorageKey = storageKeyRef.current;
      if (currentStorageKey !== null && pendingScrollTop.current !== null) {
        sessionStorage.setItem(currentStorageKey, String(pendingScrollTop.current));
        pendingScrollTop.current = null;
      }
    });
  }, []);

  const restore = useCallback((): number | null => {
    const currentStorageKey = storageKeyRef.current;

    if (!currentStorageKey) {
      return null;
    }

    const storedValue = sessionStorage.getItem(currentStorageKey);

    if (storedValue === null) {
      return null;
    }

    const value = Number(storedValue);
    return Number.isFinite(value) ? value : null;
  }, []);

  return storageKey ? { save, restore } : null;
}
