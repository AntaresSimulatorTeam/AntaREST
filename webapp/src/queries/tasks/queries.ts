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
import { getTask, getTasks } from "@/services/api/tasks";
import type { GetTasksParams, Task } from "@/services/api/tasks/types";
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
      queryFn: () => getTask({ id }),
    });
  },
};
