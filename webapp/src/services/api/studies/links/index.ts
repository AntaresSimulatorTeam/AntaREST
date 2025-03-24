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

import { format } from "@/utils/stringUtils";
import client from "../../client";
import type {
  CreateLinkParams,
  DeleteLinkParams,
  GetLinkParams,
  GetLinksParams,
  Link,
  LinkDTO,
  UpdateLinkParams,
} from "./types";
import { _formatLinkDTO, parseLinkId } from "./utils";

const LINKS_URL = "/v1/studies/{studyId}/links";
const LINK_URL = `${LINKS_URL}/{areaFrom}/{areaTo}`;

export async function createLink({ studyId, ...body }: CreateLinkParams) {
  const url = format(LINKS_URL, { studyId });
  const { data } = await client.post<LinkDTO>(url, body);
  return _formatLinkDTO(data);
}

export async function getLinks({ studyId }: GetLinksParams) {
  const url = format(LINKS_URL, { studyId });
  const { data } = await client.get<LinkDTO[]>(url);
  return data.map(_formatLinkDTO);
}

export async function getLink({ studyId, linkId }: GetLinkParams) {
  const links = await getLinks({ studyId });
  const link = links.find(({ id }) => id === linkId);

  if (!link) {
    throw new Error(`Link ${linkId} not found`);
  }

  return link;
}

export async function updateLink({ studyId, linkId, config }: UpdateLinkParams) {
  const [areaFrom, areaTo] = parseLinkId(linkId);
  const url = format(LINK_URL, { studyId, areaFrom, areaTo });

  const { data } = await client.put<LinkDTO>(url, config);

  return _formatLinkDTO(data);
}

/**
 * Deletes the link between the two specified areas.
 *
 * @param params - The parameters.
 * @param params.studyId - The study ID.
 * @param params.linkId - The link ID.
 * @returns The deleted link id (format: `${areaFromId}%${areaToId}`)
 */
export async function deleteLink({ studyId, linkId }: DeleteLinkParams) {
  const [areaFrom, areaTo] = parseLinkId(linkId);
  const url = format(LINK_URL, { studyId, areaFrom, areaTo });

  const { data } = await client.delete<Link["id"]>(url);

  return data;
}
