import { StudyMetadata } from "../../../../../../common/types";
import client from "../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum PriceTakingOrder {
  DENS = "DENS",
  Load = "Load",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AdequacyPatchFormFields {
  // Version 830
  enableAdequacyPatch: boolean;
  ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch: boolean;
  ntcBetweenPhysicalAreasOutAdequacyPatch: boolean;
  // Version 850
  priceTakingOrder: PriceTakingOrder;
  includeHurdleCostCsr: boolean;
  checkCsrCostFunction: boolean;
  thresholdInitiateCurtailmentSharingRule: number;
  thresholdDisplayLocalMatchingRuleViolations: number;
  thresholdCsrVariableBoundsRelaxation: number;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const PRICE_TAKING_ORDER_OPTIONS = Object.values(PriceTakingOrder);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/adequacypatch/form`;
}

export async function getAdequacyPatchFormFields(
  studyId: StudyMetadata["id"]
): Promise<AdequacyPatchFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setAdequacyPatchFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<AdequacyPatchFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
