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

import { toSemanticVersion } from "@/utils/versionUtils";
import type { SolverPresets, SolverPresetsDTO } from "./types";

export function adaptSolverPresetsDtoToSolverPresets(dto: SolverPresetsDTO): SolverPresets {
  return {
    ...dto,
    // The API don't follow semantic versioning format, minor and patch components may be missing
    minAntaresVersion: dto.minAntaresVersion ? toSemanticVersion(dto.minAntaresVersion) : undefined,
    maxAntaresVersion: dto.maxAntaresVersion ? toSemanticVersion(dto.maxAntaresVersion) : undefined,
  };
}
