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

import { z } from "zod";
import { TaskStatus, TaskType } from "./constants";

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const taskResultSchema = z
  .object({
    success: z.boolean(),
    message: z.string(),
    return_value: z.string().optional(),
  })
  .transform((dto) => ({
    success: dto.success,
    message: dto.message,
    returnValue: dto.return_value,
  }));

export const taskLogSchema = z.object({
  id: z.string(),
  message: z.string(),
});

export const taskSchema = z
  .object({
    id: z.string(),
    name: z.string(),
    status: z.enum(TaskStatus),
    type: z.string().optional(),
    owner: z.number().optional(),
    ref_id: z.string().optional(),
    creation_date_utc: z.string(),
    completion_date_utc: z.string().optional(),
    progress: z.number().optional(),
    result: taskResultSchema.optional(),
    logs: z.array(taskLogSchema).optional(),
  })
  .transform((dto) => ({
    id: dto.id,
    name: dto.name,
    status: dto.status,
    type: dto.type,
    owner: dto.owner,
    refId: dto.ref_id,
    creationDateUtc: dto.creation_date_utc,
    completionDateUtc: dto.completion_date_utc,
    progress: dto.progress,
    result: dto.result,
    logs: dto.logs,
  }));

export const tasksSchema = z.array(taskSchema);

////////////////////////////////////////////////////////////////
// Request Schemas
////////////////////////////////////////////////////////////////

export const getTasksParamsSchema = z.object({
  status: z.array(z.enum(TaskStatus)).optional(),
  type: z.array(z.enum(TaskType)).optional(),
  name: z.string().optional(),
  studyId: z.string().optional(),
  fromCreationDateUtc: z.number().optional(),
  toCreationDateUtc: z.number().optional(),
  fromCompletionDateUtc: z.number().optional(),
  toCompletionDateUtc: z.number().optional(),
});

export const getTaskParamsSchema = z.object({
  id: z.string(),
  waitForCompletion: z.boolean().optional(),
  withLogs: z.boolean().optional(),
  timeout: z.number().optional(),
});
