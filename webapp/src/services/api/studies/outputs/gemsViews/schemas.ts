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

const aggregationPatternSchema = z.object({
  id: z.string(),
  /** True when the pattern aggregates across scenarios. */
  scenario: z.boolean(),
  timeGranularity: z.enum(["hour", "day", "week", "month", "year"]),
});

const viewLocationsSchema = z.object({
  /** The union of locations found across this view's result files. */
  metricsLocation: z.array(z.object({ id: z.string() })),
  aggregationPatterns: z.array(aggregationPatternSchema),
});

export const gemsViewsSchema = z.array(
  z.object({
    taxonomy: z.string(),
    viewIds: z.record(z.string(), viewLocationsSchema),
  }),
);

// The backend serializes preparation responses separately from the camelCase metadata.
export const gemsViewsPreparationSchema = z
  .discriminatedUnion("status", [
    z.object({ status: z.literal("NOT_FOUND"), task_id: z.null() }),
    z.object({ status: z.literal("IN_PROGRESS"), task_id: z.string().min(1) }),
  ])
  .transform(({ status, task_id: taskId }) =>
    status === "IN_PROGRESS" ? { status, taskId } : { status },
  );
