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

import type {
  ExportMpsOption830,
  LegacyTransmissionCapacities,
  SimplexOptimizationRange,
  TransmissionCapacities840,
  UnfeasibleProblemBehavior,
} from "@/services/api/studies/config/optimization/types";
import type { BooleanToStringOrIdentity } from "@/utils/tsUtils";

export const UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS: readonly UnfeasibleProblemBehavior[] = [
  "warning-dry",
  "warning-verbose",
  "error-dry",
  "error-verbose",
];

export const SIMPLEX_OPTIMIZATION_RANGE_OPTIONS: readonly SimplexOptimizationRange[] = [
  "day",
  "week",
];

export const LEGACY_TRANSMISSION_CAPACITIES_OPTIONS: ReadonlyArray<
  BooleanToStringOrIdentity<LegacyTransmissionCapacities>
> = ["true", "false", "infinite"];

export const TRANSMISSION_CAPACITIES_OPTIONS: readonly TransmissionCapacities840[] = [
  "local-values",
  "null-for-all-links",
  "infinite-for-all-links",
  "null-for-physical-links",
  "infinite-for-physical-links",
];

export const EXPORT_MPS_OPTIONS: readonly ExportMpsOption830[] = [
  "none",
  "optim-1",
  "optim-2",
  "both-optims",
];
