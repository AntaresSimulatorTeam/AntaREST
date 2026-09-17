/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { ListViewItem } from "@/components/page/list/ListView";
import type { Output } from "@/services/api/studies/outputs/types";
import type { AreaWithId, District, LinkElement } from "@/types/types";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ListType = "areas" | "links" | "synthesis";
export type DataType = "values" | "details" | "details-res" | "id" | "details-STstorage";
export type GridType = "areas" | "links" | "digest" | "thermal";
export type Frequency = "hourly" | "daily" | "weekly" | "monthly" | "annual";
export type MonteCarloMode = "mc-ind" | "mc-all" | "variable-per-variable";
export type Item = AreaWithId | District | LinkElement;

interface CreateItemOutputDataPathParams {
  output: Output;
  item: Item;
  dataType: DataType;
  frequency: Frequency;
  year?: number;
}

interface CreateSynthesisOutputDataPathParams {
  output: Output;
  gridType: GridType;
}

type CreateOutputDataPathParams =
  | CreateItemOutputDataPathParams
  | CreateSynthesisOutputDataPathParams;

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SYNTHESIS_ITEMS = [
  {
    id: "areas",
    label: "Areas synthesis",
    data: "areas",
  },
  {
    id: "links",
    label: "Links synthesis",
    data: "links",
  },
  {
    id: "digest",
    label: "Digest",
    data: "digest",
  },
  {
    id: "thermal",
    label: "Thermal synthesis",
    data: "thermal",
  },
] as const satisfies Array<ListViewItem<GridType>>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function createOutputDataPath(params: CreateItemOutputDataPathParams): string;
export function createOutputDataPath(params: CreateSynthesisOutputDataPathParams): string;

export function createOutputDataPath(params: CreateOutputDataPathParams): string {
  const { output } = params;
  const mode = output.mode === "Adequacy" ? "adequacy" : "economy";
  const basePath = `output/${output.id}/${mode}`;

  if ("item" in params) {
    const { item, dataType, frequency, year } = params;

    const isYearPeriod = year && year > 0;
    const periodFolder = isYearPeriod
      ? `mc-ind/${Math.min(year, output.nbYears).toString().padStart(5, "0")}`
      : "mc-all";
    const itemType = isLink(item) ? "links" : "areas";
    const itemFolder = isLink(item) ? `${item.area1}/${item.area2}` : item.id;

    return `${basePath}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${frequency}`;
  }

  // Synthesis path
  return `${basePath}/mc-all/grid/${params.gridType}`;
}

export function isArea(item: Item): item is AreaWithId {
  return "links" in item;
}

export function isDistrict(item: Item): item is District {
  return "addAreas" in item;
}

export function isAreaOrDistrict(item: Item): item is AreaWithId | District {
  return isArea(item) || isDistrict(item);
}

export function isLink(item: Item): item is LinkElement {
  return "area1" in item;
}
