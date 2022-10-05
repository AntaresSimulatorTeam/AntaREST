import { StudyMetadata } from "../../../../../../common/types";
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

enum UnitCommitmentMode {
  Fast = "fast",
  Accurate = "accurate",
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
export const HYDRO_HEURISTIC_POLICY_OPTIONS =
  Object.values(HydroHeuristicPolicy);
export const HYDRO_PRICING_MODE_OPTIONS = Object.values(HydroPricingMode);
export const POWER_FLUCTUATIONS_OPTIONS = Object.values(PowerFluctuation);
export const SHEDDING_POLICY_OPTIONS = Object.values(SheddingPolicy);
export const RESERVE_MANAGEMENT_OPTIONS = Object.values(ReserveManagement);
export const UNIT_COMMITMENT_MODE_OPTIONS = Object.values(UnitCommitmentMode);
export const SIMULATION_CORES_OPTIONS = Object.values(SimulationCore);
export const RENEWABLE_GENERATION_OPTIONS = Object.values(
  RenewableGenerationModeling
);

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AdvancedParamsFormFields {
  accuracyOnCorrelation: string;
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

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/advanced_parameters`;
}

export async function getAdvancedParamsFormFields(
  studyId: StudyMetadata["id"]
): Promise<AdvancedParamsFormFields> {
  const res = await client.get(makeRequestURL(studyId));

  // Get array of values from accuracyOnCorrelation string as expected for the SelectFE component
  const accuracyOnCorrelation = res.data.accuracyOnCorrelation
    .split(/\s*,\s*/)
    .filter((v: string) => v.trim());

  return { ...res.data, accuracyOnCorrelation };
}

export function setAdvancedParamsFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<AdvancedParamsFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
