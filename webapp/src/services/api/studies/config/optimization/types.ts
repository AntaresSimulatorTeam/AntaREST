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

import type { StudyMetadata } from "@/types/types";
import type { BooleanToStringOrIdentity } from "@/utils/tsUtils";

export type UnfeasibleProblemBehavior =
  | "warning-dry"
  | "warning-verbose"
  | "error-dry"
  | "error-verbose";

export type SimplexOptimizationRange = "day" | "week";

export type LegacyTransmissionCapacities = boolean | "infinite";

// Since v8.4
export type TransmissionCapacities840 =
  | "local-values"
  | "null-for-all-links"
  | "infinite-for-all-links"
  | "null-for-physical-links"
  | "infinite-for-physical-links";

// Before v8.4 only `LegacyTransmissionCapacities' values were allowed.
// Since v8.4 only `TransmissionCapacities840` values are allowed.
export type TransmissionCapacities = LegacyTransmissionCapacities | TransmissionCapacities840;

// Since v8.3
export type ExportMpsOption830 = "none" | "optim-1" | "optim-2" | "both-optims";

// Before v8.3 only boolean values were allowed.
// Since v8.3 `ExportMpsOption830` values are allowed in addition to boolean value.
// `true` is equivalent to "both-optims" and `false` is equivalent to "none".
export type ExportMpsOption = boolean | ExportMpsOption830;

export interface OptimizationDTO {
  bindingConstraints: boolean;
  hurdleCosts: boolean;
  transmissionCapacities: TransmissionCapacities;
  thermalClustersMinStablePower: boolean;
  thermalClustersMinUdTime: boolean;
  dayAheadReserve: boolean;
  primaryReserve: boolean;
  strategicReserve: boolean;
  spinningReserve: boolean;
  exportMps: ExportMpsOption;
  unfeasibleProblemBehavior: UnfeasibleProblemBehavior;
  simplexOptimizationRange: SimplexOptimizationRange;
}

export interface OptimizationForm extends Omit<OptimizationDTO, "transmissionCapacities"> {
  transmissionCapacities: BooleanToStringOrIdentity<TransmissionCapacities>;
}

export interface BaseOptimizationParams {
  studyId: StudyMetadata["id"];
}

export interface SetOptimizationParams extends BaseOptimizationParams {
  values: Partial<OptimizationDTO>;
}

export interface GetOptimizationFormParams extends BaseOptimizationParams {
  studyVersion: string;
}

export interface SetOptimizationFormParams extends BaseOptimizationParams {
  values: Partial<OptimizationForm>;
  studyVersion: string;
}
