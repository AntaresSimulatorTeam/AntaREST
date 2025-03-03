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

import * as R from "ramda";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

import type { StudyMetadata } from "../../../../../../types/types";
import client from "../../../../../../services/api/client";

enum UnfeasibleProblemBehavior {
  WarningDry = "warning-dry",
  WarningVerbose = "warning-verbose",
  ErrorDry = "error-dry",
  ErrorVerbose = "error-verbose",
}

enum SimplexOptimizationRange {
  Day = "day",
  Week = "week",
}

enum LegacyTransmissionCapacities {
  True = "true",
  False = "false",
  Infinite = "infinite",
}

enum TransmissionCapacities {
  LocalValues = "local-values",
  NullForAllLinks = "null-for-all-links",
  InfiniteForAllLinks = "infinite-for-all-links",
  NullForPhysicalLinks = "null-for-physical-links",
  InfiniteForPhysicalLinks = "infinite-for-physical-links",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface OptimizationFormFields {
  bindingConstraints: boolean;
  hurdleCosts: boolean;
  transmissionCapacities: boolean | LegacyTransmissionCapacities.Infinite | TransmissionCapacities;
  thermalClustersMinStablePower: boolean;
  thermalClustersMinUdTime: boolean;
  dayAheadReserve: boolean;
  primaryReserve: boolean;
  strategicReserve: boolean;
  spinningReserve: boolean;
  exportMps: boolean;
  unfeasibleProblemBehavior: UnfeasibleProblemBehavior;
  simplexOptimizationRange: SimplexOptimizationRange;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS = Object.values(UnfeasibleProblemBehavior);
export const SIMPLEX_OPTIMIZATION_RANGE_OPTIONS = Object.values(SimplexOptimizationRange);
export const LEGACY_TRANSMISSION_CAPACITIES_OPTIONS = Object.values(LegacyTransmissionCapacities);
export const TRANSMISSION_CAPACITIES_OPTIONS = Object.values(TransmissionCapacities);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/optimization/form`;
}

export async function getOptimizationFormFields(
  studyId: StudyMetadata["id"],
): Promise<OptimizationFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setOptimizationFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<OptimizationFormFields>,
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}

export const toBooleanIfNeeded = R.cond([
  [R.equals("true"), R.T],
  [R.equals("false"), R.F],
  [R.T, R.identity],
]);
