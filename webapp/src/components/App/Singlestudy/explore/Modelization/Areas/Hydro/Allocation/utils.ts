import { StudyMetadata, Area } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AllocationField {
  areaId: string;
  coefficient: number;
}
export interface AllocationFormFields {
  allocation: AllocationField[];
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/allocation`;
}

export async function getAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): Promise<AllocationFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export function setAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: Partial<AllocationFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId), values);
}
