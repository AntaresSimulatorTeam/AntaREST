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

import type { StudyMetadata } from "@/types/types";
import client from "../../client";
import type { CreateLinkParams, DeleteLinkParams, LinkDTO } from "./types";

export async function createLink(params: CreateLinkParams) {
  const { studyId, ...body } = params;
  const { data } = await client.post<LinkDTO>(`/v1/studies/${params.studyId}/links`, body);
  return data;
}

export async function getLinks(params: { studyId: StudyMetadata["id"] }) {
  const { data } = await client.get<LinkDTO[]>(`/v1/studies/${params.studyId}/links`);
  return data;
}

/**
 * Deletes the link between the two specified areas.
 *
 * @param params - The parameters.
 * @param params.studyId - The study ID.
 * @param params.areaFrom - The from area name.
 * @param params.areaTo - The to area name.
 * @returns The deleted link id (format: `${areaFromId}%${areaToId}`)
 */
export async function deleteLink(params: DeleteLinkParams) {
  const { studyId, areaFrom, areaTo } = params;
  const { data } = await client.delete<string>(
    `/v1/studies/${studyId}/links/${areaFrom}/${areaTo}`,
  );
  return data;
}
