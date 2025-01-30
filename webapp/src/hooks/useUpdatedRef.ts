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

import { useLayoutEffect, useRef } from "react";

/**
 * Hook that returns a mutable ref that automatically updates its value.
 *
 * @param value - The value to store in the ref.
 * @returns The mutable ref.
 */
function useUpdatedRef<T>(value: T): React.MutableRefObject<T> {
  const ref = useRef(value);

  // `useLayoutEffect` runs before `useEffect`. So `useLayoutEffect` is used to make sure
  // the value is up-to-date before any other code runs.
  useLayoutEffect(() => {
    ref.current = value;
  });

  return ref;
}

export default useUpdatedRef;
