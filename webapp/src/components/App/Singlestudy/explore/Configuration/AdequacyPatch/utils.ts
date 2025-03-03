/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { StudyMetadata } from "../../../../../../types/types";
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
  studyId: StudyMetadata["id"],
): Promise<AdequacyPatchFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setAdequacyPatchFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<AdequacyPatchFormFields>,
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
