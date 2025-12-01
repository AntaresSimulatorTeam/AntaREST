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

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

import type { DeepPartial } from "redux";
import type { Area, StudyMetadata } from "../../../../../../../types/types";
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
  spreadUnsuppliedEnergyCost: number;
  spreadSpilledEnergyCost: number;
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

function makeRequestURL(studyId: StudyMetadata["id"], areaId: Area["name"]): string {
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
