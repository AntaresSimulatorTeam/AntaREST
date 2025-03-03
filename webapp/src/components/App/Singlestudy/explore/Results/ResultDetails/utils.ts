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

import type { Area, LinkElement, Simulation } from "../../../../../../types/types";

export enum OutputItemType {
  Areas = "areas",
  Links = "links",
  Synthesis = "synthesis",
}

export enum DataType {
  General = "values",
  Thermal = "details",
  Renewable = "details-res",
  Record = "id",
  STStorage = "details-STstorage",
}

export enum Timestep {
  Hourly = "hourly",
  Daily = "daily",
  Weekly = "weekly",
  Monthly = "monthly",
  Annual = "annual",
}

interface Params {
  output: Simulation & { id: string };
  item: (Area & { id: string }) | LinkElement;
  dataType: DataType;
  timestep: Timestep;
  year?: number;
}

export const MAX_YEAR = 99999;

export function createPath(params: Params): string {
  const { output, item, dataType, timestep, year } = params;
  const { id, mode } = output;
  const isYearPeriod = year && year > 0;
  const periodFolder = isYearPeriod
    ? `mc-ind/${Math.min(year, output.nbyears).toString().padStart(5, "0")}`
    : "mc-all";
  const isLink = "area1" in item;
  const itemType = isLink ? OutputItemType.Links : OutputItemType.Areas;
  const itemFolder = isLink ? `${item.area1}/${item.area2}` : item.id;

  return `output/${id}/${mode}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${timestep}`;
}

export const SYNTHESIS_ITEMS = [
  {
    id: "areas",
    name: "Areas",
    label: "Areas synthesis",
  },
  {
    id: "links",
    name: "Links",
    label: "Links synthesis",
  },
  {
    id: "digest",
    name: "Digest",
    label: "Digest",
  },
  {
    id: "thermal",
    name: "Thermal",
    label: "Thermal synthesis",
  },
];

// Allow the possibilty to use OR operator on search using pipe
export function matchesSearchTerm(text: string, searchTerm: string): boolean {
  const searchTerms = searchTerm.split("|").map((term) => term.trim().toLowerCase());

  return searchTerms.some((term) => text.toLowerCase().includes(term));
}
