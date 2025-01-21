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

import { useRef, type useEffect } from "react";
import { useUpdateEffect } from "react-use";

/**
 * Hook that runs the effect only at the first dependencies update.
 * It behaves like the `useEffect` hook, but it skips the initial run,
 * and the runs following the first update.
 *
 * @param effect - The effect function to run.
 * @param deps - An array of dependencies to watch for changes.
 */
const useUpdateEffectOnce: typeof useEffect = (effect, deps) => {
  const hasUpdated = useRef(false);

  useUpdateEffect(() => {
    if (!hasUpdated.current) {
      hasUpdated.current = true;
      return effect();
    }
  }, deps);
};

export default useUpdateEffectOnce;
