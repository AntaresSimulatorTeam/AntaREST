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
  getReserve,
  getReserveGlobalParameters,
  getReserves,
  getReservesCertifications,
  getReservesSymmetries,
} from "@/services/api/studies/areas/reserves";
import type {
  CertificationProductionType,
  Reserve,
  SymmetryProductionType,
} from "@/services/api/studies/areas/reserves/types";
import { getOptimization } from "@/services/api/studies/config/optimization";
import type { AreaWithId } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { EXTERNALLY_MUTATED, queryListOptions } from "../utils";
import { reserveKeys } from "./keys";
import type { Study } from "@/services/api/studies/types";

export const reserveQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryListOptions({
      queryKey: reserveKeys.list(studyId, areaId),
      queryFn: () => getReserves({ studyId, areaId }),
    });
  },
  detail: (studyId: Study["id"], areaId: AreaWithId["id"], reserveId: Reserve["id"]) => {
    return queryOptions({
      queryKey: reserveKeys.detail(studyId, areaId, reserveId),
      queryFn: () => getReserve({ studyId, areaId, reserveId }),
    });
  },
  globalParameters: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: reserveKeys.globalParameters(studyId, areaId),
      queryFn: () => getReserveGlobalParameters({ studyId, areaId }),
    });
  },
  enabled: (studyId: Study["id"]) => {
    return queryOptions({
      queryKey: reserveKeys.enabled(studyId),
      queryFn: () => getOptimization({ studyId }).then((o) => !!o.includeReserves),
    });
  },
  certifications: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    productionType: CertificationProductionType,
  ) => {
    return queryOptions({
      queryKey: reserveKeys.certifications(studyId, areaId, productionType),
      queryFn: () => getReservesCertifications({ studyId, areaId, productionType }),
      // Deleting a cluster elsewhere (Thermals page, table mode) cascades to its
      // certifications server-side without invalidating this cache.
      ...EXTERNALLY_MUTATED,
    });
  },
  symmetries: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    productionType: SymmetryProductionType,
  ) => {
    return queryOptions({
      queryKey: reserveKeys.symmetries(studyId, areaId, productionType),
      queryFn: () => getReservesSymmetries({ studyId, areaId, productionType }),
      // Deleting a cluster or a reserve elsewhere cascades to its symmetries
      // server-side without invalidating this cache.
      ...EXTERNALLY_MUTATED,
    });
  },
};
