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
import { nullishToOptional } from "../../../utils/zodUtils";
import { TaskStatus, TaskType } from "./constants";

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const taskResultSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  returnValue: nullishToOptional(z.string()),
});

export const taskLogSchema = z.object({
  id: z.string(),
  message: z.string(),
});

export const taskSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.enum(TaskStatus),
  type: z.enum(TaskType).optional(),
  owner: z.number().optional(),
  refId: nullishToOptional(z.string()),
  creationDateUtc: z.string(),
  completionDateUtc: z.string().optional(),
  progress: nullishToOptional(z.number()),
  result: taskResultSchema.optional(),
  logs: nullishToOptional(z.array(taskLogSchema)),
});

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
