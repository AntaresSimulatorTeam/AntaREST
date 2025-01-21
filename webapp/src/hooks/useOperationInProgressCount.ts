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

import { useMemo, useState } from "react";
import * as R from "ramda";

/**
 * Hook to tracks the number of CRUD operations in progress.
 *
 * @returns An object containing methods to increment, decrement,
 * and retrieve the count of each operation type.
 */
function useOperationInProgressCount() {
  const [opsInProgressCount, setOpsInProgressCount] = useState({
    create: 0,
    read: 0,
    update: 0,
    delete: 0,
  });

  const makeOperationMethods = (operation: keyof typeof opsInProgressCount) => ({
    increment: (number = 1) => {
      setOpsInProgressCount((prev) => ({
        ...prev,
        [operation]: prev[operation] + number,
      }));
    },
    decrement: (number = 1) => {
      setOpsInProgressCount((prev) => ({
        ...prev,
        [operation]: Math.max(prev[operation] - number, 0),
      }));
    },
    total: opsInProgressCount[operation],
  });

  const methods = useMemo(
    () => ({
      createOps: makeOperationMethods("create"),
      readOps: makeOperationMethods("read"),
      updateOps: makeOperationMethods("update"),
      deleteOps: makeOperationMethods("delete"),
      totalOps: Object.values(opsInProgressCount).reduce(R.add, 0),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [opsInProgressCount],
  );

  return methods;
}

export default useOperationInProgressCount;
