import { type StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface InflowStructureFields {
  interMonthlyCorrelation: number;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"], areaId: string): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/inflowstructure`;
}

export async function getInflowStructureFields(
  studyId: StudyMetadata["id"],
  areaId: string,
): Promise<InflowStructureFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export function updatetInflowStructureFields(
  studyId: StudyMetadata["id"],
  areaId: string,
  values: InflowStructureFields,
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId), values);
}
