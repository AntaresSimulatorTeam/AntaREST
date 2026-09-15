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
import type {
  createReserveParamsSchema,
  productionTypeSchema,
  reserveCertificationSchema,
  reserveGlobalParametersSchema,
  reserveSchema,
  reserveTypeSchema,
  reservesCertificationsSchema,
  reservesSymmetriesSchema,
  storageReserveCertificationSchema,
  thermalReserveCertificationSchema,
  updateReserveGlobalParametersSchema,
  updateReserveParamsSchema,
} from "./schemas";
import type { Study } from "../../types";

export type ReserveType = z.infer<typeof reserveTypeSchema>;
export type Reserve = z.infer<typeof reserveSchema>;
export type ReserveGlobalParameters = z.infer<typeof reserveGlobalParametersSchema>;
export type ProductionType = z.infer<typeof productionTypeSchema>;
export type ThermalReserveCertification = z.infer<typeof thermalReserveCertificationSchema>;
export type StorageReserveCertification = z.infer<typeof storageReserveCertificationSchema>;
export type ReserveCertification = z.infer<typeof reserveCertificationSchema>;
export type ReservesCertifications = z.infer<typeof reservesCertificationsSchema>;
export type ReservesSymmetries = z.infer<typeof reservesSymmetriesSchema>;

export type CreateReserveData = z.infer<typeof createReserveParamsSchema>;
export type UpdateReserveData = z.infer<typeof updateReserveParamsSchema>;
export type UpdateReserveGlobalParametersData = z.infer<typeof updateReserveGlobalParametersSchema>;

export interface ReservesAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetReserveParams extends ReservesAreaParams {
  reserveId: Reserve["id"];
}

export interface CreateReserveParams extends ReservesAreaParams {
  data: CreateReserveData;
}

export interface UpdateReserveParams extends ReservesAreaParams {
  reserveId: Reserve["id"];
  data: UpdateReserveData;
}

export interface DeleteReservesParams extends ReservesAreaParams {
  reserveIds: Array<Reserve["id"]>;
}

export interface UpdateReserveGlobalParametersParams extends ReservesAreaParams {
  data: UpdateReserveGlobalParametersData;
}

export interface ReservesProductionTypeParams extends ReservesAreaParams {
  productionType: ProductionType;
}

export interface UpdateReservesCertificationsParams extends ReservesProductionTypeParams {
  data: ReservesCertifications;
}

export interface UpdateReservesSymmetriesParams extends ReservesProductionTypeParams {
  data: ReservesSymmetries;
}
