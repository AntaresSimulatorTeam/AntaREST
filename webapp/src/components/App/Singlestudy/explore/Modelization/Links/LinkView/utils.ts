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

import type { FieldValues } from "react-hook-form";
import { getStudyData } from "../../../../../../../services/api/study";
import type { FilteringType } from "../../../common/types";

type TransCapacitiesType = "infinite" | "ignore" | "enabled";
type AssetType = "ac" | "dc" | "gaz" | "virt";
type LinkStyleType = "plain" | "dash" | "dot" | "dotdash";

export interface LinkType {
  "hurdles-cost": boolean;
  "loop-flow": boolean;
  "use-phase-shifter": boolean;
  "transmission-capacities": TransCapacitiesType;
  "asset-type": AssetType;
  "link-style": LinkStyleType;
  "link-width": number;
  colorr: number;
  colorg: number;
  colorb: number;
  "filter-synthesis": string;
  "filter-year-by-year": string;
}

export interface LinkFields extends FieldValues {
  hurdleCost: boolean;
  loopFlows: boolean;
  pst: boolean;
  type: string;
  transmissionCapa: string;
  filterSynthesis: FilteringType[];
  filterByYear: FilteringType[];
}

export type LinkPath = Omit<Record<keyof LinkFields, string>, "name">;

export function getLinkPath(area1: string, area2: string): LinkPath {
  const pathPrefix = `input/links/${area1.toLowerCase()}/properties/${area2.toLowerCase()}`;
  return {
    hurdleCost: `${pathPrefix}/hurdles-cost`,
    loopFlows: `${pathPrefix}/loop-flow`,
    pst: `${pathPrefix}/use-phase-shifter`,
    type: pathPrefix, // TODO `${pathPrefix}/asset-type`? (cf. create_link.py)
    transmissionCapa: `${pathPrefix}/transmission-capacities`,
    filterSynthesis: `${pathPrefix}/filter-synthesis`,
    filterByYear: `${pathPrefix}/filter-year-by-year`,
  };
}

export async function getDefaultValues(
  studyId: string,
  area1: string,
  area2: string,
): Promise<LinkFields> {
  // Path
  const pathPrefix = `input/links/${area1.toLowerCase()}/properties/${area2.toLowerCase()}`;
  // Fetch fields
  const fields: LinkType = await getStudyData(studyId, pathPrefix, 3);

  // Return element
  return {
    hurdleCost: fields["hurdles-cost"],
    loopFlows: fields["loop-flow"],
    pst: fields["use-phase-shifter"],
    type: fields["asset-type"],
    transmissionCapa: fields["transmission-capacities"],
    filterSynthesis: fields["filter-synthesis"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
    filterByYear: fields["filter-year-by-year"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
  };
}

export default {};
