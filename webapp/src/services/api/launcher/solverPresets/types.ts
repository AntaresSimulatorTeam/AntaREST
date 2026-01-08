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

type SolverParams = Record<string, string>;

export interface SolverPresetsDTO {
  id: string;
  name: string;
  linearSolver: string;
  minAntaresVersion?: string;
  maxAntaresVersion?: string;
  linearSolverParamOptim1?: SolverParams;
  linearSolverParamOptim2?: SolverParams;
  linearSolverParam?: SolverParams;
  useOptim1BasisNextWeek?: boolean;
  useOptim1BasisOptim2?: boolean;
}

// This type uses semantic versioning (see `adaptSolverPresetsDtoToSolverPresets()` function)
export type SolverPresets = SolverPresetsDTO;

export type SolverPresetsCreationDTO = Omit<SolverPresetsDTO, "id">;
