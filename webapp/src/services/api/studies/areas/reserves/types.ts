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
  reserveGlobalParametersSchema,
  reserveSchema,
  reserveTypeSchema,
  updateReserveGlobalParametersSchema,
  updateReserveParamsSchema,
} from "./schemas";
import type { Study } from "../../types";

export type ReserveType = z.infer<typeof reserveTypeSchema>;
export type Reserve = z.infer<typeof reserveSchema>;
export type ReserveGlobalParameters = z.infer<typeof reserveGlobalParametersSchema>;

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
