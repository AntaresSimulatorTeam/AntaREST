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
import { useMemo } from "react";
import { useScrollPersistence } from "./useScrollPersistence";

/**
 * Persists and restores the scroll position of an `OverlayScrollbars` container
 * via `sessionStorage`. Pass the returned `EventListeners` to `CustomScrollbar`'s
 * `events` prop:
 *
 * ```tsx
 * const scrollEvents = useScrollRestorationOS("my-panel");
 * <CustomScrollbar events={scrollEvents}>…</CustomScrollbar>
 * ```
 *
 * @param key - Unique, stable ID for this scrollable region. `undefined` disables persistence.
 * @returns OverlayScrollbars `EventListeners` to spread onto `CustomScrollbar`, or `undefined`.
 */
export function useScrollRestorationOS(key: string | undefined): EventListeners | undefined {
  const persistence = useScrollPersistence(key);

  return useMemo<EventListeners | undefined>(() => {
    if (!persistence) {
      return undefined;
    }

    const { save, restore } = persistence;

    return {
      initialized(instance) {
        const scrollTop = restore();

        if (scrollTop !== null) {
          instance.elements().scrollOffsetElement.scrollTo({ top: scrollTop, behavior: "instant" });
        }
      },

      scroll(instance) {
        save(instance.elements().scrollOffsetElement.scrollTop);
      },
    };
  }, [persistence]);
}
