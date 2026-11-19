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

import { queryOptions } from "@tanstack/react-query";
import { secondsToMilliseconds } from "date-fns";
import { getTask, getTasks } from "@/services/api/tasks";
import type { GetTasksParams, Task } from "@/services/api/tasks/types";
import { isTaskFinished } from "@/services/api/tasks/utils";
import { taskKeys } from "./keys";

export const taskQueries = {
  list: (params: GetTasksParams = {}) => {
    return queryOptions({
      queryKey: taskKeys.list(params),
      queryFn: () => getTasks(params),
    });
  },

  detail: (id: Task["id"]) => {
    return queryOptions({
      queryKey: taskKeys.detail(id),
      queryFn: ({ signal }) => getTask({ id }, signal),
    });
  },

  // Polling is opt-in. Both observers share the same task detail cache.
  monitor: (id: Task["id"]) =>
    queryOptions({
      ...taskQueries.detail(id),
      staleTime: 0,
      refetchInterval: ({ state }) =>
        state.status === "success" && state.data && !isTaskFinished(state.data)
          ? secondsToMilliseconds(2)
          : false,
    }),
};
