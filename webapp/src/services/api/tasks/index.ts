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

import client from "../client";
import type { GetTaskParams, GetTasksParams, TaskDTO } from "./types";

export async function getTasks(params: GetTasksParams) {
  const res = await client.post<TaskDTO[]>("/v1/tasks", {
    status: params.status,
    type: params.type,
    name: params.name,
    ref_id: params.studyId,
    from_creation_date_utc: params.fromCreationDateUtc,
    to_creation_date_utc: params.toCreationDateUtc,
    from_completion_date_utc: params.fromCompletionDateUtc,
    to_completion_date_utc: params.toCompletionDateUtc,
  });

  return res.data;
}

export async function getTask(params: GetTaskParams) {
  const { id, ...queryParams } = params;

  const res = await client.get<TaskDTO>(`/v1/tasks/${id}`, {
    params: {
      wait_for_completion: queryParams.waitForCompletion,
      with_logs: queryParams.withLogs,
      timeout: queryParams.timeout,
    },
  });

  return res.data;
}
