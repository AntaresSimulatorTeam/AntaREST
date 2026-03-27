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

import type { z } from "zod";
import type { TaskStatus, TaskType } from "./constants";
import type {
  getTaskParamsSchema,
  getTasksParamsSchema,
  taskLogSchema,
  taskResultSchema,
  taskSchema,
} from "./schemas";

////////////////////////////////////////////////////////////////
// Union Types
////////////////////////////////////////////////////////////////

export type TaskStatusValue = (typeof TaskStatus)[keyof typeof TaskStatus];
export type TaskTypeValue = (typeof TaskType)[keyof typeof TaskType];

////////////////////////////////////////////////////////////////
// Response Types
////////////////////////////////////////////////////////////////

export type TaskResult = z.infer<typeof taskResultSchema>;
export type TaskLog = z.infer<typeof taskLogSchema>;
export type Task = z.infer<typeof taskSchema>;

////////////////////////////////////////////////////////////////
// Request params
////////////////////////////////////////////////////////////////

export type GetTasksParams = z.infer<typeof getTasksParamsSchema>;
export type GetTaskParams = z.infer<typeof getTaskParamsSchema>;
