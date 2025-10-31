/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type {
  SolverPresets,
  SolverPresetsCreation,
  SolverPresetsCreationDTO,
  SolverPresetsDTO,
} from "./types";

export function adaptSolverPresetsDtoToSolverPresets(dto: SolverPresetsDTO): SolverPresets {
  return {
    id: dto.id,
    name: dto.name,
    linearSolver: dto.linear_solver,
    minAntaresVersion: dto.min_antares_version,
    maxAntaresVersion: dto.max_antares_version,
    linearSolverParamOptim1: dto.linear_solver_param_optim_1,
    linearSolverParamOptim2: dto.linear_solver_param_optim_2,
    linearSolverParam: dto.linear_solver_param,
    useOptim1BasisNextWeek: dto.use_optim_1_basis_next_week,
    useOptim1BasisOptim2: dto.use_optim_1_basis_optim_2,
  };
}

export function adaptSolverPresetsCreationToDto(
  solverPresetsCreation: SolverPresetsCreation,
): SolverPresetsCreationDTO {
  return {
    name: solverPresetsCreation.name,
    linear_solver: solverPresetsCreation.linearSolver,
    min_antares_version: solverPresetsCreation.minAntaresVersion,
    max_antares_version: solverPresetsCreation.maxAntaresVersion,
    linear_solver_param_optim_1: solverPresetsCreation.linearSolverParamOptim1,
    linear_solver_param_optim_2: solverPresetsCreation.linearSolverParamOptim2,
    linear_solver_param: solverPresetsCreation.linearSolverParam,
    use_optim_1_basis_next_week: solverPresetsCreation.useOptim1BasisNextWeek,
    use_optim_1_basis_optim_2: solverPresetsCreation.useOptim1BasisOptim2,
  };
}
