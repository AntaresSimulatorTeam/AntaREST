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

export const OUTPUT_ITEM_TYPES = ["areas", "links", "synthesis"] as const;

export const DATA_TYPES = ["values", "details", "details-res", "id", "details-STstorage"] as const;

export const TIMESTEPS = ["hourly", "daily", "weekly", "monthly", "annual"] as const;

export const MONTE_CARLO_MODES = ["mc-ind", "mc-all", "variable-per-variable"] as const;

export type OutputItemType = (typeof OUTPUT_ITEM_TYPES)[number];
export type DataType = (typeof DATA_TYPES)[number];
export type Timestep = (typeof TIMESTEPS)[number];
export type MonteCarloMode = (typeof MONTE_CARLO_MODES)[number];

interface Params {
  output: Partial<Simulation> & { id: string; name: string };
  item: (Area & { id: string }) | LinkElement;
  dataType: DataType;
  timestep: Timestep;
  year?: number;
}

export const MAX_YEAR = 99999;

export function createPath(params: Params): string {
  const { output, item, dataType, timestep, year } = params;
  const { id, mode = "economy" } = output;
  const isYearPeriod = year && year > 0;
  const periodFolder = isYearPeriod
    ? `mc-ind/${Math.min(year, output.nbyears || MAX_YEAR)
        .toString()
        .padStart(5, "0")}`
    : "mc-all";
  const isLink = "area1" in item;
  const itemType = isLink ? "links" : "areas";
  const itemFolder = isLink ? `${item.area1}/${item.area2}` : item.id;

  return `output/${id}/${mode.toLowerCase()}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${timestep}`;
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

export function matchesSearchTerm(text: string, searchTerm: string): boolean {
  const searchTerms = searchTerm.split("|").map((term) => term.trim().toLowerCase());
  return searchTerms.some((term) => text.toLowerCase().includes(term));
}

export function getFirstVariableForItem(
  variablesMetadata: { mcAll: unknown; mcInd: unknown } | null,
  itemType: OutputItemType,
  selectedItemId: string,
): string {
  if (!variablesMetadata || !selectedItemId) {
    return "";
  }

  const data = variablesMetadata.mcInd as {
    areas: Array<{ name: string; variables: string[] }>;
    links: Array<{ area1Name: string; area2Name: string; variables: string[] }>;
  };

  if (itemType === "areas") {
    const area = data.areas.find((a) => a.name === selectedItemId);
    return area?.variables[0] || "";
  }

  if (itemType === "links") {
    const link = data.links.find(
      (l) => l.area1Name === selectedItemId || l.area2Name === selectedItemId,
    );
    return link?.variables[0] || "";
  }

  return "";
}
