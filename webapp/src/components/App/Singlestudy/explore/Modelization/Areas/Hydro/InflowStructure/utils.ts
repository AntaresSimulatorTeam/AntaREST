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

import { type StudyMetadata } from "../../../../../../../../types/types";
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
  return `v1/studies/${studyId}/areas/${areaId}/hydro/inflow-structure`;
}

export async function getInflowStructureFields(
  studyId: StudyMetadata["id"],
  areaId: string,
): Promise<InflowStructureFields> {
  const res = await client.get(makeRequestURL(studyId, areaId));
  return res.data;
}

export function updateInflowStructureFields(
  studyId: StudyMetadata["id"],
  areaId: string,
  values: InflowStructureFields,
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId), values);
}
