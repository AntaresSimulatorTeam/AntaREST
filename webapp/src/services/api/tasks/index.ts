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
 * @param params.id - Task identifier.
 * @param params.waitForCompletion - Wait until the task reaches a terminal state.
 * @param params.withLogs - Include task logs in the response.
 * @param params.timeout - Maximum number of seconds to wait for completion.
 * @param signal - Cancels the request when the caller stops observing the task.
 * @returns The task matching the given ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function getTask(
  { id, waitForCompletion, withLogs, timeout }: GetTaskParams,
  signal?: AbortSignal,
) {
  const res = await client.get(`/v1/tasks/${id}`, {
    signal,
    params: {
      wait_for_completion: waitForCompletion,
      with_logs: withLogs,
      timeout,
    },
  });

  return taskSchema.parse(res.data);
}
