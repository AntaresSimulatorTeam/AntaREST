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
import { HYDRO_ASSET_ID } from "./constants";

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

////////////////////////////////////////////////////////////////
// Production Types
////////////////////////////////////////////////////////////////

// The production types that can participate in reserves. Each one has its own
// certifications and symmetries endpoints (`.../reserves/{certifications|symmetries}/{type}`).
// To add a new type: add it here, give it a certification schema below, a wire codec if its
// payload isn't asset-keyed, and an entry in the UI registry (see `-productionTypes.ts`).
export const productionTypeSchema = z.enum(["thermals", "storages", "hydro"]);

////////////////////////////////////////////////////////////////
// Certifications
////////////////////////////////////////////////////////////////

export const thermalReserveCertificationSchema = z.object({
  maxPower: z.number(),
  maxPowerOff: z.number(),
  participationCost: z.number(),
  participationCostOff: z.number(),
});

// Shared by short-term storages and hydro (long-term storage).
export const storageReserveCertificationSchema = z.object({
  participationCost: z.number(),
  maxRelease: z.number(),
  maxStore: z.number(),
});

export const reserveCertificationSchema = z.union([
  thermalReserveCertificationSchema,
  storageReserveCertificationSchema,
]);

// Normalized shape, shared by every production type:
// { [reserveId]: { [assetId]: certification } }.
// An asset absent from a reserve's record has no active certification for it.
export const reservesCertificationsSchema = z.record(
  z.string(),
  z.record(z.string(), reserveCertificationSchema),
);

function assetKeyedCertificationsSchema<T extends z.ZodType>(certificationSchema: T) {
  return z.record(z.string(), z.record(z.string(), certificationSchema));
}

const hydroReservesCertificationsWireSchema = z.record(
  z.string(),
  storageReserveCertificationSchema,
);

// Wire <-> normalized: { [reserveId]: certification } <-> { [reserveId]: { hydro: certification } }.
const hydroReservesCertificationsCodec = z.codec(
  hydroReservesCertificationsWireSchema,
  assetKeyedCertificationsSchema(storageReserveCertificationSchema),
  {
    decode: (wire) =>
      Object.fromEntries(
        Object.entries(wire).map(([reserveId, certification]) => [
          reserveId,
          { [HYDRO_ASSET_ID]: certification },
        ]),
      ),
    encode: (data) =>
      Object.fromEntries(
        Object.entries(data).flatMap(([reserveId, certifications]) => {
          const certification = certifications[HYDRO_ASSET_ID];
          return certification ? [[reserveId, certification]] : [];
        }),
      ),
  },
);

// One codec per production type, from the wire payload to the normalized shape.
// `codec.parse(wire)` decodes, `z.encode(codec, data)` re-encodes for a PUT.
export const reservesCertificationsCodecs: Record<
  z.infer<typeof productionTypeSchema>,
  z.ZodType<z.infer<typeof reservesCertificationsSchema>>
> = {
  thermals: assetKeyedCertificationsSchema(thermalReserveCertificationSchema),
  storages: assetKeyedCertificationsSchema(storageReserveCertificationSchema),
  hydro: hydroReservesCertificationsCodec,
};

////////////////////////////////////////////////////////////////
// Symmetries
////////////////////////////////////////////////////////////////

// One symmetry is the list of reserves it participates in. The backend requires at least 2
// distinct reserve IDs per symmetry
const symmetriesListSchema = z.array(z.array(z.string()));

// Normalized shape, shared by every production type:
// { [assetId]: [reserveId, ...][] }.
export const reservesSymmetriesSchema = z.record(z.string(), symmetriesListSchema);

// Wire <-> normalized: [reserveId, ...][] <-> { hydro: [reserveId, ...][] }.
const hydroReservesSymmetriesCodec = z.codec(symmetriesListSchema, reservesSymmetriesSchema, {
  decode: (wire): Record<string, string[][]> => (wire.length > 0 ? { [HYDRO_ASSET_ID]: wire } : {}),
  encode: (data) => data[HYDRO_ASSET_ID] ?? [],
});

export const reservesSymmetriesCodecs: Record<
  z.infer<typeof productionTypeSchema>,
  z.ZodType<z.infer<typeof reservesSymmetriesSchema>>
> = {
  thermals: reservesSymmetriesSchema,
  storages: reservesSymmetriesSchema,
  hydro: hydroReservesSymmetriesCodec,
};

////////////////////////////////////////////////////////////////
// Input Schemas
////////////////////////////////////////////////////////////////

export const createReserveParamsSchema = reserveSchema
  .omit({ id: true })
  .partial()
  .required({ name: true, type: true });

export const updateReserveParamsSchema = reserveSchema.omit({ id: true, name: true }).partial();

export const updateReserveGlobalParametersSchema = reserveGlobalParametersSchema.partial();
