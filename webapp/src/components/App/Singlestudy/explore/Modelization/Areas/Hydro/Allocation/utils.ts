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

import type { StudyMetadata, Area } from "../../../../../../../../types/types";
import client from "../../../../../../../../services/api/client";
import type { MatrixDataDTO } from "../../../../../../../common/Matrix/shared/types";
import type { AreaCoefficientItem } from "../utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface AllocationFormFields {
  allocation: AreaCoefficientItem[];
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"], areaId: Area["name"]): string {
  return `v1/studies/${studyId}/areas/${areaId}/hydro/allocation/form`;
}

export async function getAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): Promise<AllocationFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export async function setAllocationFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  values: AllocationFormFields,
): Promise<AllocationFormFields> {
  const res = await client.put(makeRequestURL(studyId, areaId), values);
  return res.data;
}

export const getAllocationMatrix = async (studyId: StudyMetadata["id"]): Promise<MatrixDataDTO> => {
  const res = await client.get(`v1/studies/${studyId}/areas/hydro/allocation/matrix`);
  return res.data;
};
