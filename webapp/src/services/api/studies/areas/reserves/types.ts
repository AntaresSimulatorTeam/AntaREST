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

import type { AreaWithId } from "@/types/types";
import type { z } from "zod";
import type { Study } from "../../types";
import type {
  productionTypeSchema,
  reserveCertificationSchema,
  reserveCreationSchema,
  reserveGlobalParametersSchema,
  reserveGlobalParametersUpdateSchema,
  reserveSchema,
  reserveTypeSchema,
  reserveUpdateSchema,
  reservesCertificationsSchema,
  reservesSymmetriesSchema,
  storageReserveCertificationSchema,
  thermalReserveCertificationSchema,
} from "./schemas";

export type ReserveType = z.infer<typeof reserveTypeSchema>;
export type Reserve = z.infer<typeof reserveSchema>;
export type ReserveGlobalParameters = z.infer<typeof reserveGlobalParametersSchema>;
export type ProductionType = z.infer<typeof productionTypeSchema>;
export type ThermalReserveCertification = z.infer<typeof thermalReserveCertificationSchema>;
export type StorageReserveCertification = z.infer<typeof storageReserveCertificationSchema>;
export type ReserveCertification = z.infer<typeof reserveCertificationSchema>;
/** Includes the keys of each certification model, rather than only their shared keys. */
export type ReserveCertificationField<
  TCertification extends ReserveCertification = ReserveCertification,
> = TCertification extends ReserveCertification ? keyof TCertification & string : never;
export type ReservesCertifications = z.infer<typeof reservesCertificationsSchema>;
export type ReservesSymmetries = z.infer<typeof reservesSymmetriesSchema>;

export type ReserveCreation = z.infer<typeof reserveCreationSchema>;
export type ReserveUpdate = z.infer<typeof reserveUpdateSchema>;
export type ReserveGlobalParametersUpdate = z.infer<typeof reserveGlobalParametersUpdateSchema>;

export interface ReservesParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface ReserveParams extends ReservesParams {
  reserveId: Reserve["id"];
}

export interface CreateReserveParams extends ReservesParams {
  data: ReserveCreation;
}

export interface UpdateReserveParams extends ReserveParams {
  data: ReserveUpdate;
}

export interface DeleteReservesParams extends ReservesParams {
  reserveIds: Array<Reserve["id"]>;
}

export interface UpdateReserveGlobalParametersParams extends ReservesParams {
  data: ReserveGlobalParametersUpdate;
}

export interface ReservesProductionTypeParams extends ReservesParams {
  productionType: ProductionType;
}

export interface UpdateReservesCertificationsParams extends ReservesProductionTypeParams {
  data: ReservesCertifications;
}

export interface UpdateReservesSymmetriesParams extends ReservesProductionTypeParams {
  data: ReservesSymmetries;
}
