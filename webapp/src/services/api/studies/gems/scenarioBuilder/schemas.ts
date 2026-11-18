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

export const scenarioNameSchema = z.string().regex(/^[a-z0-9_]+$/);

const scenarioEntrySchema = z.object({
  scenario: z.number().int().nonnegative(), // Year
  timeSeriesIndex: z.number().int().nonnegative(),
});

export const scenarioSchema = z.array(scenarioEntrySchema);

const scenariosByNameSchema = z.record(scenarioNameSchema, scenarioSchema);

export const scenarioBuilderSchema = z.object({
  scenarios: scenariosByNameSchema,
});
