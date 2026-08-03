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

import z from "zod";

const outputVariablesViewStatusSchema = z.enum(["NOT_FOUND", "IN_PROGRESS"]);

export const outputVariablesViewResponseSchema = z
  .object({
    status: outputVariablesViewStatusSchema,
    task_id: z.string().nullish(),
  })
  .transform((input) => ({
    status: input.status,
    taskId: input.task_id,
  }));
