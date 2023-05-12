import {
  StudyMetadata,
  Area,
  MatrixType,
} from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";
import { AreaCoefficientItem } from "../utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AllocationFormFields {
  allocation: AreaCoefficientItem[];
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/allocation/form`;
}

export async function getAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"]
): Promise<AllocationFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export async function setAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: AllocationFormFields
): Promise<AllocationFormFields> {
  const res = await client.put(makeRequestURL(studyId, areaId), values);
  return res.data;
}

export const getAllocationMatrix = async (
  studyId: StudyMetadata["id"]
): Promise<MatrixType> => {
  const res = await client.get(
    `v1/studies/${studyId}/areas/hydro/allocation/matrix`
  );
  return res.data;
};
