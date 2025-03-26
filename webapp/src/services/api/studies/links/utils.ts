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

import type { FilterLink, Link, LinkDTO } from "./types";

const LINK_ID_SEPARATOR = "%";

/**
 * Creates a link ID.
 *
 * Note: The format is based on the return value of `deleteLink`,
 * which is the only API endpoint that returns a link ID.
 *
 * @param areaFrom - The from area name.
 * @param areaTo - The to area name.
 * @returns The link ID.
 */
export function createLinkId(areaFrom: Link["area1"], areaTo: Link["area2"]) {
  return `${areaFrom}${LINK_ID_SEPARATOR}${areaTo}`;
}

export function parseLinkId(linkId: Link["id"]) {
  return linkId.split(LINK_ID_SEPARATOR);
}

////////////////////////////////////////////////////////////////
// Private
////////////////////////////////////////////////////////////////

function _formatLinkFilter(filter: string) {
  return filter
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean) as FilterLink;
}

export function _formatLinkDTO(dto: LinkDTO) {
  const { filterSynthesis, filterYearByYear, ...rest } = dto;
  const link: Link = {
    // The ID should ideally be returned by the API
    id: createLinkId(dto.area1, dto.area2),
    ...rest,
  };

  // TODO: fix the API to return an array like indicated in the specs
  if (typeof dto.filterSynthesis === "string") {
    link.filterSynthesis = _formatLinkFilter(dto.filterSynthesis);
  }
  if (typeof dto.filterYearByYear === "string") {
    link.filterYearByYear = _formatLinkFilter(dto.filterYearByYear);
  }

  return link;
}
