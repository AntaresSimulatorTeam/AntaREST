import { StudyMetadata, Area } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";
import { AreaCoefficientItem } from "../utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface CorrelationFormFields {
  correlation: AreaCoefficientItem[];
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/correlation/form`;
}

export async function getCorrelationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): Promise<CorrelationFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export async function setCorrelationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: CorrelationFormFields
): Promise<CorrelationFormFields> {
  const res = await client.put(makeRequestURL(studyId, areaId), values);
  return res.data;
}
