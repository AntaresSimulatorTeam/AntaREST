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

import client from "../../client";
import { adaptSolverPresetsDtoToSolverPresets } from "./adapters";
import type { SolverPresetsCreationDTO, SolverPresetsDTO } from "./types";

const BASE_URL = "/v1/launcher/solver-presets";

export async function getSolverPresets() {
  const { data } = await client.get<SolverPresetsDTO[]>(BASE_URL);
  return data.map(adaptSolverPresetsDtoToSolverPresets);
}

export async function createSolverPresets(params: SolverPresetsCreationDTO) {
  const { data } = await client.post<SolverPresetsDTO>(BASE_URL, params);

  return data;
}
