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

import { useState } from "react";
import { useUpdateEffect } from "react-use";

/**
 * Hook that returns a memoized value with semantic guarantee.
 *
 * Semantic guarantee is not provided by `useMemo`, which is solely used
 * for performance optimization (cf. https://react.dev/reference/react/useMemo#caveats).
 *
 * @param factory - A function that returns the value to memoize.
 * @param deps - Dependencies that trigger the memoization.
 * @returns The memoized value.
 */
function useSafeMemo<T>(factory: () => T, deps: React.DependencyList): T {
  const [state, setState] = useState(factory);

  useUpdateEffect(() => {
    setState(factory);
  }, deps);

  return state;
}

export default useSafeMemo;
