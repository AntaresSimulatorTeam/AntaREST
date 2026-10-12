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
  thermalCreationSchema,
  thermalGroupSchema,
  thermalSchema,
  thermalUpdateSchema,
} from "./schemas";

export type ThermalGroup = z.infer<typeof thermalGroupSchema>;
export type Thermal = z.infer<typeof thermalSchema>;
export type ThermalCreation = z.infer<typeof thermalCreationSchema>;
export type ThermalUpdate = z.infer<typeof thermalUpdateSchema>;

export interface ThermalsAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetThermalParams extends ThermalsAreaParams {
  thermalId: Thermal["id"];
}

export interface CreateThermalParams extends ThermalsAreaParams {
  values: ThermalCreation;
}

export interface UpdateThermalParams extends GetThermalParams {
  values: ThermalUpdate;
}

export interface DuplicateThermalParams extends GetThermalParams {
  newName: Thermal["name"];
}

export interface DeleteThermalsParams extends ThermalsAreaParams {
  thermalIds: Array<Thermal["id"]>;
}
