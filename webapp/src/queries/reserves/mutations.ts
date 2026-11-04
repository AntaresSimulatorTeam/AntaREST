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

import {
  createReserve,
  deleteReserves,
  updateReserve,
  updateReserveGlobalParameters,
  updateReservesCertifications,
  updateReservesSymmetries,
} from "@/services/api/studies/areas/reserves";
import type {
  CreateReserveParams,
  DeleteReservesParams,
  ProductionType,
  Reserve,
  UpdateReserveGlobalParametersParams,
  UpdateReserveParams,
  UpdateReservesCertificationsParams,
  UpdateReservesSymmetriesParams,
} from "@/services/api/studies/areas/reserves/types";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { reserveKeys } from "./keys";

export const reserveMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.create(studyId, areaId),
      mutationFn: (params: Omit<CreateReserveParams, "studyId" | "areaId">) => {
        return createReserve({ ...params, studyId, areaId });
      },
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"], reserveId: Reserve["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.update(studyId, areaId, reserveId),
      mutationFn: (params: Omit<UpdateReserveParams, "studyId" | "areaId" | "reserveId">) => {
        return updateReserve({ ...params, studyId, areaId, reserveId });
      },
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.delete(studyId, areaId),
      mutationFn: (params: Omit<DeleteReservesParams, "studyId" | "areaId">) => {
        return deleteReserves({ ...params, studyId, areaId });
      },
    });
  },
  updateGlobalParameters: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.updateGlobalParameters(studyId, areaId),
      mutationFn: (params: Omit<UpdateReserveGlobalParametersParams, "studyId" | "areaId">) => {
        return updateReserveGlobalParameters({ ...params, studyId, areaId });
      },
    });
  },
  updateCertifications: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    productionType: ProductionType,
  ) => {
    return mutationOptions({
      mutationKey: reserveKeys.updateCertifications(studyId, areaId, productionType),
      mutationFn: (
        params: Omit<UpdateReservesCertificationsParams, "studyId" | "areaId" | "productionType">,
      ) => {
        return updateReservesCertifications({ ...params, studyId, areaId, productionType });
      },
    });
  },
  updateSymmetries: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    productionType: ProductionType,
  ) => {
    return mutationOptions({
      mutationKey: reserveKeys.updateSymmetries(studyId, areaId, productionType),
      mutationFn: (
        params: Omit<UpdateReservesSymmetriesParams, "studyId" | "areaId" | "productionType">,
      ) => {
        return updateReservesSymmetries({ ...params, studyId, areaId, productionType });
      },
    });
  },
};
