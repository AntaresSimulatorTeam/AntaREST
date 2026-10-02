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
  renewableClusterCreationSchema,
  renewableClusterSchema,
  renewableClusterUpdateSchema,
  renewableGroupSchema,
} from "./schemas";

export type RenewableGroup = z.infer<typeof renewableGroupSchema>;
export type RenewableCluster = z.infer<typeof renewableClusterSchema>;
export type RenewableClusterCreation = z.input<typeof renewableClusterCreationSchema>;
export type RenewableClusterUpdate = z.input<typeof renewableClusterUpdateSchema>;

export interface RenewablesAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetRenewableClusterParams extends RenewablesAreaParams {
  clusterId: RenewableCluster["id"];
}

export interface CreateRenewableClusterParams extends RenewablesAreaParams {
  values: RenewableClusterCreation;
}

export interface UpdateRenewableClusterParams extends GetRenewableClusterParams {
  values: RenewableClusterUpdate;
}

export interface DuplicateRenewableClusterParams extends GetRenewableClusterParams {
  newName: RenewableCluster["name"];
}

export interface DeleteRenewableClustersParams extends RenewablesAreaParams {
  clusterIds: Array<RenewableCluster["id"]>;
}
