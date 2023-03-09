import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum ClusterGroup {
  WindOnshore = "Wind Onshore",
  WindOffshore = "Wind Offshore",
  SolarThermal = "Solar Thermal",
  SolarPV = "Solar PV",
  SolarRooftop = "Solar Rooftop",
  OtherRES1 = "Other RES 1",
  OtherRES2 = "Other RES 2",
  OtherRES3 = "Other RES 3",
  OtherRES4 = "Other RES 4",
}

enum TimeSeriesInterpretation {
  PowerGeneration = "power-generation",
  ProductionFactor = "production-factor",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface RenewableFormFields {
  name: string;
  group: string;
  tsInterpretation: TimeSeriesInterpretation;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const CLUSTER_GROUP_OPTIONS = Object.values(ClusterGroup);
export const TS_INTERPRETATION_OPTIONS = Object.values(
  TimeSeriesInterpretation
);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"]
): string {
  return `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable/${clusterId}/form`;
}

export async function getRenewableFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"]
): Promise<RenewableFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId, clusterId));
  return res.data;
}

export function updateRenewableFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  values: Partial<RenewableFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId, clusterId), values);
}
