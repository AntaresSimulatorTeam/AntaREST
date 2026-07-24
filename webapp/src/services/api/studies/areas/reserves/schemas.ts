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

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const reserveTypeSchema = z.enum(["up", "down"]);

export const reserveSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: reserveTypeSchema,
  failureCost: z.number(),
  spillageCost: z.number(),
  referenceActivationDuration: z.number(),
  powerActivationRatio: z.number(),
  energyActivationRatio: z.number(),
});

export const reservesSchema = z.array(reserveSchema);

export const reserveGlobalParametersSchema = z.object({
  referenceActivationDurationUp: z.number(),
  energyActivationRatioUp: z.number(),
  referenceActivationDurationDown: z.number(),
  energyActivationRatioDown: z.number(),
});

// Production types with released certification endpoints.
// "storages" and "hydro" are coming soon: add them here once their endpoints are released.
export const certificationProductionTypeSchema = z.enum(["thermals"]);

export const reserveCertificationSchema = z.object({
  maxPower: z.number(),
  maxPowerOff: z.number(),
  participationCost: z.number(),
  participationCostOff: z.number(),
});

// Shape: { [reserveId]: { [clusterId]: certification } }.
// A cluster absent from a reserve's record has no active certification for it.
export const reserveCertificationsSchema = z.record(
  z.string(),
  z.record(z.string(), reserveCertificationSchema),
);

////////////////////////////////////////////////////////////////
// Input Schemas
////////////////////////////////////////////////////////////////

export const createReserveParamsSchema = reserveSchema
  .omit({ id: true })
  .partial()
  .required({ name: true, type: true });

export const updateReserveParamsSchema = reserveSchema.omit({ id: true, name: true }).partial();

export const updateReserveGlobalParametersSchema = reserveGlobalParametersSchema.partial();
