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

type SolverParams = Record<string, string>;

// Supports version formats like '[major].[minor]' or '[major].[minor].[patch]'.
// Note: it works without adding a third number because number can be a integer or a float.
type SolverVersionStr = `${number}.${number}`;

export interface SolverPresetsDTO {
  id: string;
  name: string;
  linear_solver: string;
  min_antares_version?: SolverVersionStr;
  max_antares_version?: SolverVersionStr;
  linear_solver_param_optim_1?: SolverParams;
  linear_solver_param_optim_2?: SolverParams;
  linear_solver_param?: SolverParams;
  use_optim_1_basis_next_week?: boolean;
  use_optim_1_basis_optim_2?: boolean;
}

export interface SolverPresets {
  id: string;
  name: string;
  linearSolver: string;
  minAntaresVersion?: SolverVersionStr;
  maxAntaresVersion?: SolverVersionStr;
  linearSolverParamOptim1?: SolverParams;
  linearSolverParamOptim2?: SolverParams;
  linearSolverParam?: SolverParams;
  useOptim1BasisNextWeek?: boolean;
  useOptim1BasisOptim2?: boolean;
}

export type SolverPresetsCreation = Omit<SolverPresets, "id">;

export type SolverPresetsCreationDTO = Omit<SolverPresetsDTO, "id">;
