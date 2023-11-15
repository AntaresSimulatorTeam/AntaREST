import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const RENEWABLE_GROUPS = [
  "Wind Onshore",
  "Wind Offshore",
  "Solar Thermal",
  "Solar PV",
  "Solar Rooftop",
  "Other RES 1",
  "Other RES 2",
  "Other RES 3",
  "Other RES 4",
] as const;

export const TS_INTERPRETATION_OPTIONS = [
  "power-generation",
  "production-factor",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

type TimeSeriesInterpretationOption =
  (typeof TS_INTERPRETATION_OPTIONS)[number];

export interface RenewableFormFields {
  name: string;
  group: string;
  tsInterpretation: TimeSeriesInterpretationOption;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string {
  return `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable/${clusterId}/form`;
}

export async function getRenewableFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): Promise<RenewableFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId, clusterId));
  return res.data;
}

export function updateRenewableFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  values: Partial<RenewableFormFields>,
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId, clusterId), values);
}
