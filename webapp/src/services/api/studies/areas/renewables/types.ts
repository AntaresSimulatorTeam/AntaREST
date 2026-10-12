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
  renewableCreationSchema,
  renewableGroupSchema,
  renewableSchema,
  renewableUpdateSchema,
} from "./schemas";

export type RenewableGroup = z.infer<typeof renewableGroupSchema>;
export type Renewable = z.infer<typeof renewableSchema>;
export type RenewableCreation = z.input<typeof renewableCreationSchema>;
export type RenewableUpdate = z.input<typeof renewableUpdateSchema>;

export interface RenewablesAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetRenewableParams extends RenewablesAreaParams {
  renewableId: Renewable["id"];
}

export interface CreateRenewableParams extends RenewablesAreaParams {
  values: RenewableCreation;
}

export interface UpdateRenewableParams extends GetRenewableParams {
  values: RenewableUpdate;
}

export interface DuplicateRenewableParams extends GetRenewableParams {
  newName: Renewable["name"];
}

export interface DeleteRenewablesParams extends RenewablesAreaParams {
  renewableIds: Array<Renewable["id"]>;
}
