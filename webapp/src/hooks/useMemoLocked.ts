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

/* 
 "You may rely on useMemo as a performance optimization, not as a semantic
 guarantee. In the future, React may choose to “forget” some previously
 memoized values and recalculate them on next render, e.g. to free memory for
 offscreen components. Write your code so that it still works without useMemo —
 and then add it to optimize performance."
 Source: https://reactjs.org/docs/hooks-reference.html#usememo
*/

function useMemoLocked<T>(factory: () => T): T {
  // eslint-disable-next-line react/hook-use-state
  const [state] = useState(factory);
  return state;
}

export default useMemoLocked;
