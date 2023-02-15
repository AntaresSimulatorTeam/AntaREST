import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

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

enum TsMode {
  PowerGeneration = "power-generation",
  ProductionFactor = "production-factor",
}

export interface RenewableFormFields {
  name: string;
  group: string;
  tsInterpretation: string;
  enabled: boolean;
  unitcount: number;
  nominalcapacity: number;
}

export const CLUSTER_GROUP_OPTIONS = Object.values<ClusterGroup>(ClusterGroup);
export const TS_MODE_OPTIONS = Object.values<TsMode>(TsMode);

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
