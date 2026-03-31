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

import client from "../client";
import { taskSchema, tasksSchema } from "./schemas";
import type { GetTaskParams, GetTasksParams } from "./types";

/**
 * GET /v1/tasks - Lists tasks matching the given filters.
 *
 * @param params - The filters to apply when listing tasks.
 * @returns The list of tasks matching the given filters.
 * @throws If the response doesn't match the expected schema.
 */
export async function getTasks(params: GetTasksParams) {
  const res = await client.get("/v1/tasks", {
    params: {
      status: params.status,
      type: params.type,
      name: params.name,
      ref_id: params.studyId,
      from_creation_date_utc: params.fromCreationDateUtc,
      to_creation_date_utc: params.toCreationDateUtc,
      from_completion_date_utc: params.fromCompletionDateUtc,
      to_completion_date_utc: params.toCompletionDateUtc,
    },
    // FastAPI expects repeated params for arrays: ?status=1&status=2
    paramsSerializer: { indexes: null },
  });

  return tasksSchema.parse(res.data);
}

/**
 * GET /v1/tasks/{id} - Gets a single task by ID.
 *
 * @param params - The parameters to use when retrieving the task.
 * @returns The task matching the given ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function getTask(params: GetTaskParams) {
  const { id, waitForCompletion, withLogs, timeout } = params;

  const res = await client.get(`/v1/tasks/${id}`, {
    params: {
      wait_for_completion: waitForCompletion,
      with_logs: withLogs,
      timeout,
    },
  });

  return taskSchema.parse(res.data);
}
