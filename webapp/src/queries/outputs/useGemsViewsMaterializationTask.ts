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

import type { OutputParams } from "@/services/api/studies/outputs/types";
import type { Task } from "@/services/api/tasks/types";
import { isTaskFinished } from "@/services/api/tasks/utils";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { taskQueries } from "../tasks/queries";
import { outputQueries } from "./queries";

// Kept here temporarily to test task polling and metadata refresh before the GEMS view exists.
// TODO: Move this hook next to the GemsViews component when it is added.
export default function useGemsViewsMaterializationTask(
  { studyId, outputId }: OutputParams,
  taskId: Task["id"],
) {
  const client = useQueryClient();
  const task = useQuery(taskQueries.monitor(taskId));
  const isFinished = task.data !== undefined && isTaskFinished(task.data);

  useEffect(() => {
    if (!isFinished) {
      return;
    }

    const { queryKey } = outputQueries.gemsViews({ studyId, outputId });
    const views = client.getQueryData(queryKey);

    // Even a failed task can race another preparation that successfully produced metadata.
    if (views?.status === "IN_PROGRESS" && views.taskId === taskId) {
      void client.invalidateQueries({ queryKey, exact: true });
    }
  }, [client, studyId, outputId, taskId, isFinished]);

  return task;
}
