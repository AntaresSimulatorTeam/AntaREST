////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

import { DeepPartial } from "redux";
import { Area, StudyMetadata } from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

enum AdequacyPatchMode {
  Outside = "outside",
  Inside = "inside",
  Virtual = "virtual",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface PropertiesFormFields {
  color: string;
  posX: number;
  posY: number;
  energyCostUnsupplied: number;
  energyCostSpilled: number;
  nonDispatchPower: boolean;
  dispatchHydroPower: boolean;
  otherDispatchPower: boolean;
  filterSynthesis: string[];
  filterByYear: string[];
  // For study versions >= 830
  adequacyPatchMode: AdequacyPatchMode;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const ADEQUACY_PATCH_OPTIONS = Object.values(AdequacyPatchMode);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string {
  return `/v1/studies/${studyId}/areas/${areaId}/properties/form`;
}

export async function getPropertiesFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): Promise<PropertiesFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export function setPropertiesFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: DeepPartial<PropertiesFormFields>,
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId), values);
}
