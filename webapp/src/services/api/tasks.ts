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

import { TaskDTO, TaskStatus } from "../../common/types";
import client from "./client";

export const getStudyRunningTasks = async (sid: string): Promise<TaskDTO[]> => {
  const res = await client.post("/v1/tasks", {
    ref_id: sid,
    status: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllRunningTasks = async (): Promise<TaskDTO[]> => {
  const res = await client.post("/v1/tasks", {
    status: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllMiscRunningTasks = async (): Promise<TaskDTO[]> => {
  const res = await client.post("/v1/tasks", {
    status: [
      TaskStatus.RUNNING,
      TaskStatus.PENDING,
      TaskStatus.FAILED,
      TaskStatus.COMPLETED,
    ],
    type: ["COPY", "ARCHIVE", "UNARCHIVE", "SCAN", "UPGRADE_STUDY"],
  });
  return res.data;
};

export const getTask = async (
  id: string,
  withLogs = false,
): Promise<TaskDTO> => {
  const res = await client.get(`/v1/tasks/${id}?with_logs=${withLogs}`);
  return res.data;
};

export const getProgress = async (id: string): Promise<number> => {
  const res = await client.get(`/v1/launcher/jobs/${id}/progress`);
  return res.data;
};

export default {};
