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
  createThermalClusterParamsSchema,
  thermalClusterSchema,
  thermalGroupSchema,
  updateThermalClusterParamsSchema,
} from "./schemas";

export type ThermalGroup = z.infer<typeof thermalGroupSchema>;
export type ThermalCluster = z.infer<typeof thermalClusterSchema>;
export type ThermalClusterCreation = z.infer<typeof createThermalClusterParamsSchema>;
export type ThermalClusterUpdate = z.infer<typeof updateThermalClusterParamsSchema>;

export interface ThermalsAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetThermalClusterParams extends ThermalsAreaParams {
  clusterId: ThermalCluster["id"];
}

export interface CreateThermalClusterParams extends ThermalsAreaParams {
  values: ThermalClusterCreation;
}

export interface UpdateThermalClusterParams extends GetThermalClusterParams {
  values: ThermalClusterUpdate;
}

export interface DuplicateThermalClusterParams extends GetThermalClusterParams {
  newName: ThermalCluster["name"];
}

export interface DeleteThermalClustersParams extends ThermalsAreaParams {
  clusterIds: Array<ThermalCluster["id"]>;
}
