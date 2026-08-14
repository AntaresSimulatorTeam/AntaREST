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

import type { Options } from "@/components/fieldEditors/SelectFE";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";
import {
  isAreaOrDistrict,
  isLink,
  type DataType,
  type Frequency,
  type Item,
  type MonteCarloMode,
} from "../../../../-utils";
import { isClusterDataType } from "../../utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface GetVariablesParams {
  variablesList: VariablesListDTO;
  item: Item;
  dataType: DataType;
  clusterId: string;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const MONTE_CARLO_MODE_OPTIONS = [
  { value: "mc-all", label: "Synthesis" },
  { value: "mc-ind", label: "Year by year" },
  { value: "variable-per-variable", label: (t) => t("study.outputs.variablePerVariable") },
] as const satisfies Options<MonteCarloMode>;

const DATATYPE_OPTIONS = [
  { value: "values", label: "General values" },
  { value: "details", label: "Thermal plants" },
  { value: "details-res", label: "Ren. clusters" },
  { value: "id", label: "RecordYears" },
  { value: "details-STstorage", label: "ST Storages" },
] as const satisfies Options<DataType>;

export const FREQUENCY_OPTIONS = [
  { value: "hourly", label: (t) => t("global.time.hourly") },
  { value: "daily", label: (t) => t("global.time.daily") },
  { value: "weekly", label: (t) => t("global.time.weekly") },
  { value: "monthly", label: (t) => t("global.time.monthly") },
  { value: "annual", label: (t) => t("global.time.annual") },
] as const satisfies Options<Frequency>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function getDataTypeOptions(item: Item, monteCarloMode: MonteCarloMode) {
  if (monteCarloMode === "variable-per-variable") {
    if (isAreaOrDistrict(item)) {
      return DATATYPE_OPTIONS.filter((option) => option.value !== "id");
    }

    if (isLink(item)) {
      return DATATYPE_OPTIONS.filter((option) => option.value === "values");
    }
  }

  // 'Year by year' mode
  if (monteCarloMode === "mc-ind") {
    return DATATYPE_OPTIONS.filter((option) => option.value !== "id");
  }

  return DATATYPE_OPTIONS;
}

/**
 * Checks if a link matches the selected ID (bidirectional match)
 *
 * @param area1 - First area name
 * @param area2 - Second area name
 * @param selectedId - The selected link ID to match against
 * @returns True if the link matches in either direction
 */
function isLinkMatch(area1: string, area2: string, selectedId: string): boolean {
  const linkId1 = `${area1}%${area2}`;
  const linkId2 = `${area2}%${area1}`;
  return linkId1 === selectedId || linkId2 === selectedId;
}

/**
 * Gets cluster options based on the data type.
 *
 * @param variablesList - The metadata containing all variables information.
 * @param dataType - The type of data (details, details-res, details-STstorage).
 * @param areaId - The ID of the area.
 * @returns Array of cluster options based on data type.
 */
export function getClusters(variablesList: VariablesListDTO, dataType: DataType, areaId: string) {
  const area = variablesList.mcInd.areas.find((a) => a.name === areaId);

  if (!area) {
    return [];
  }

  switch (dataType) {
    case "details":
      return area.thermalClusters || [];
    case "details-res":
      return area.renewableClusters || [];
    case "details-STstorage":
      return area.shortTermStorages || [];
    default:
      return [];
  }
}

export function getVariables(params: GetVariablesParams) {
  const { variablesList, item, dataType, clusterId } = params;
  const { mcInd } = variablesList;

  if (isAreaOrDistrict(item)) {
    if (isClusterDataType(dataType)) {
      const clusters = getClusters(variablesList, dataType, item.id);
      const cluster = clusters.find((c) => c.name === clusterId);
      return cluster?.variables || [];
    }

    const area = mcInd.areas.find((a) => a.name === item.id);
    return area?.variables || [];
  }

  if (isLink(item)) {
    const link = mcInd.links.find((link) => isLinkMatch(link.area1Name, link.area2Name, item.id));
    return link?.variables || [];
  }

  return [];
}
