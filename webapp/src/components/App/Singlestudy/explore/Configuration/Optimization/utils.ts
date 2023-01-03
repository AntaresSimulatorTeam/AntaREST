////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

import { StudyMetadata } from "../../../../../../common/types";
import client from "../../../../../../services/api/client";

enum LinkType {
  Local = "local",
  AC = "ac",
}

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
  transmissionCapacities:
    | boolean
    | LegacyTransmissionCapacities.Infinite
    | TransmissionCapacities;
  linkType: LinkType;
  thermalClustersMinStablePower: boolean;
  thermalClustersMinUdTime: boolean;
  dayAheadReserve: boolean;
  primaryReserve: boolean;
  strategicReserve: boolean;
  spinningReserve: boolean;
  exportMps: boolean;
  unfeasibleProblemBehavior: UnfeasibleProblemBehavior;
  simplexOptimizationRange: SimplexOptimizationRange;
  // version 830
  splitExportedMps?: boolean;
  enableAdequacyPatch?: boolean;
  ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch?: boolean;
  ntcBetweenPhysicalAreasOutAdequacyPatch?: boolean;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const LINK_TYPE_OPTIONS = [
  { label: "Local", value: LinkType.Local },
  { label: "AC", value: LinkType.AC },
];
export const UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS = Object.values(
  UnfeasibleProblemBehavior
);
export const SIMPLEX_OPTIMIZATION_RANGE_OPTIONS = Object.values(
  SimplexOptimizationRange
);
export const LEGACY_TRANSMISSION_CAPACITIES_OPTIONS = Object.values(
  LegacyTransmissionCapacities
);
export const TRANSMISSION_CAPACITIES_OPTIONS = Object.values(
  TransmissionCapacities
);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/optimization/form`;
}

export async function getOptimizationFormFields(
  studyId: StudyMetadata["id"]
): Promise<OptimizationFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setOptimizationFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<OptimizationFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
