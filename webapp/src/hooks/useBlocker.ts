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

import type { History, Transition } from "history";
import { useContext, useEffect } from "react";
import { UNSAFE_NavigationContext as NavigationContext } from "react-router-dom";
import useUpdatedRef from "./useUpdatedRef";

// * Workaround until it will be supported by react-router v6.
// * Based on https://ui.dev/react-router-preventing-transitions

type Blocker = (tx: Transition) => void;

function useBlocker(blocker: Blocker, when = true): void {
  const { navigator } = useContext(NavigationContext);
  const blockerRef = useUpdatedRef(blocker);

  useEffect(
    () => {
      if (!when) {
        return;
      }

      const unblock = (navigator as History).block((tx) => {
        blockerRef.current({
          ...tx,
          retry: (): void => {
            unblock();
            tx.retry();
          },
        });
      });

      return unblock;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [navigator, when],
  );
}

export default useBlocker;
