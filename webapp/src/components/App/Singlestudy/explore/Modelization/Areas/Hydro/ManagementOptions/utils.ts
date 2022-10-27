import { Area, StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum InitializeReservoirDate {
  January = 0,
  Febuary = 1,
  March = 2,
  April = 3,
  May = 4,
  June = 5,
  July = 6,
  August = 7,
  September = 8,
  October = 9,
  November = 10,
  December = 11,
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const INITIALIZE_RESERVOIR_DATE_OPTIONS = Object.entries(
  InitializeReservoirDate
)
  .splice(Object.keys(InitializeReservoirDate).length / 2)
  .map((options) => ({
    label: options[0],
    value: options[1],
  }));

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface ManagementOptionsFormFields {
  followLoad: boolean;
  useHeuristic: boolean;
  interDailyBreakdown: number;
  intraDailyModulation: number;
  reservoirCapacity: number;
  interMonthlyBreakdown: number;
  reservoir: boolean;
  hardBounds: boolean;
  pumpingEfficiency: number;
  useWater: boolean;
  initializeReservoirDate: number;
  useLeeway: boolean;
  powerToLevel: boolean;
  leewayLow: number;
  leewayUp: number;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/config`;
}

export async function getManagementOptionsFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): Promise<ManagementOptionsFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export function setManagementOptionsFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: Partial<ManagementOptionsFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId), values);
}
