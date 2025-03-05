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

import type { DeepPartial } from "react-hook-form";
import type { StudyMetadata } from "../../../../../../types/types";
import client from "../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum SpatialCorrelation {
  Wind = "wind",
  Load = "load",
  Solar = "solar",
}

enum InitialReservoirLevel {
  ColdStart = "cold start",
  HotStart = "hot start",
}

enum HydroHeuristicPolicy {
  AccommodateRulesCurves = "accommodate rule curves",
  MaximizeGeneration = "maximize generation",
}

enum HydroPricingMode {
  Fast = "fast",
  Accurate = "accurate",
}

enum PowerFluctuation {
  FreeModulations = "free modulations",
  MinimizeExcursions = "minimize excursions",
  MinimizeRamping = "minimize ramping",
}

enum SheddingPolicy {
  ShavePeaks = "shave peaks",
  MinimizeDuration = "minimize duration",
}

enum ReserveManagement {
  Global = "global",
}

export enum UnitCommitmentMode {
  Fast = "fast",
  Accurate = "accurate",
  // Since v8.8
  MILP = "milp",
}

enum SimulationCore {
  Minimum = "minimum",
  Low = "low",
  Medium = "medium",
  High = "high",
  Maximum = "maximum",
}

enum RenewableGenerationModeling {
  Aggregated = "aggregated",
  Clusters = "clusters",
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SPATIAL_CORRELATIONS_OPTIONS = Object.values(SpatialCorrelation);
export const INITIAL_RESERVOIR_OPTIONS = Object.values(InitialReservoirLevel);
export const HYDRO_HEURISTIC_POLICY_OPTIONS = Object.values(HydroHeuristicPolicy);
export const HYDRO_PRICING_MODE_OPTIONS = Object.values(HydroPricingMode);
export const POWER_FLUCTUATIONS_OPTIONS = Object.values(PowerFluctuation);
export const SHEDDING_POLICY_OPTIONS = Object.values(SheddingPolicy);
export const RESERVE_MANAGEMENT_OPTIONS = Object.values(ReserveManagement);
export const UNIT_COMMITMENT_MODE_OPTIONS = Object.values(UnitCommitmentMode);
export const SIMULATION_CORES_OPTIONS = Object.values(SimulationCore);
export const RENEWABLE_GENERATION_OPTIONS = Object.values(RenewableGenerationModeling);

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AdvancedParamsFormFields {
  accuracyOnCorrelation: string[];
  dayAheadReserveManagement: string;
  hydroHeuristicPolicy: string;
  hydroPricingMode: string;
  initialReservoirLevels: string;
  numberOfCoresMode: string;
  powerFluctuations: string;
  renewableGenerationModelling: string;
  seedHydroCosts: number;
  seedInitialReservoirLevels: number;
  seedSpilledEnergyCosts: number;
  seedThermalCosts: number;
  seedTsgenHydro: number;
  seedTsgenLoad: number;
  seedTsgenSolar: number;
  seedTsgenThermal: number;
  seedTsgenWind: number;
  seedTsnumbers: number;
  seedUnsuppliedEnergyCosts: number;
  sheddingPolicy: string;
  unitCommitmentMode: string;
}

type AdvancedParamsFormFields_RAW = Omit<AdvancedParamsFormFields, "accuracyOnCorrelation"> & {
  accuracyOnCorrelation: string;
};

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/advancedparameters/form`;
}

export async function getAdvancedParamsFormFields(studyId: StudyMetadata["id"]) {
  const { data } = await client.get<AdvancedParamsFormFields_RAW>(makeRequestURL(studyId));

  return {
    ...data,
    accuracyOnCorrelation: data.accuracyOnCorrelation
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean),
  } as AdvancedParamsFormFields;
}

export async function setAdvancedParamsFormFields(
  studyId: StudyMetadata["id"],
  values: DeepPartial<AdvancedParamsFormFields>,
) {
  const { accuracyOnCorrelation, ...rest } = values;
  const newValues: Partial<AdvancedParamsFormFields_RAW> = rest;

  if (accuracyOnCorrelation) {
    newValues.accuracyOnCorrelation = accuracyOnCorrelation.join(", ");
  }

  await client.put(makeRequestURL(studyId), newValues);
}
