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

import client from "@/services/api/client";
import type { FileStudyTreeConfigDTO, StudyMetadata } from "@/types/types";
import type { DeepPartial } from "react-hook-form";

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

export enum SheddingPolicy {
  ShavePeaks = "shave peaks",
  MinimizeDuration = "minimize duration",
  // Since v9.2
  AccurateShavePeaks = "accurate shave peaks",
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

enum HydroPmax {
  Daily = "daily",
  Hourly = "hourly",
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
export const HYDRO_PMAX_OPTIONS = Object.values(HydroPmax);
////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AdvancedParamsFormFields {
  accuracyOnCorrelation: string[];
  dayAheadReserveManagement: string;
  hydroHeuristicPolicy: string;
  hydroPricingMode: string;
  initialReservoirLevels?: string; // Not present since v9.2
  numberOfCoresMode: string;
  powerFluctuations: string;
  renewableGenerationModelling: FileStudyTreeConfigDTO["enr_modelling"];
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
  // Since v9.3
  accurateShavePeaksIncludeShortTermStorage?: boolean;
}

export interface CompatibilityParamsFormFields {
  // Since v9.2
  hydroPmax?: string;
}

/** Form values type (advanced params + compatibility params when v9.2+). */
export type AdvancedParamsFormValues = AdvancedParamsFormFields &
  Partial<CompatibilityParamsFormFields>;

type AdvancedParamsFormFields_RAW = Omit<AdvancedParamsFormFields, "accuracyOnCorrelation"> & {
  accuracyOnCorrelation: string;
};

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

function makeAdvancedParamsRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/advancedparameters/form`;
}

function makeCompatibilityRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/compatibility/form`;
}

export async function getAdvancedParamsFormFields(studyId: StudyMetadata["id"]) {
  const { data } = await client.get<AdvancedParamsFormFields_RAW>(
    makeAdvancedParamsRequestURL(studyId),
  );

  return {
    ...data,
    accuracyOnCorrelation: data.accuracyOnCorrelation
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean),
  } as AdvancedParamsFormFields;
}

export async function getCompatibilityParamsFormFields(
  studyId: StudyMetadata["id"],
): Promise<CompatibilityParamsFormFields> {
  const { data } = await client.get<CompatibilityParamsFormFields>(
    makeCompatibilityRequestURL(studyId),
  );
  return data;
}

export async function setCompatibilityParamsFormFields(
  studyId: StudyMetadata["id"],
  values: DeepPartial<CompatibilityParamsFormFields>,
) {
  await client.put(makeCompatibilityRequestURL(studyId), values);
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

  await client.put(makeAdvancedParamsRequestURL(studyId), newValues);
}
