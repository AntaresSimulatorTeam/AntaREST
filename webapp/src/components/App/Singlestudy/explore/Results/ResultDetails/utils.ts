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

import type {
  AreaVariablesDTO,
  RenewableClusterVariablesDTO,
  ShortTermStorageVariablesDTO,
  ThermalClusterVariablesDTO,
  VariableViewParams,
  VariablesListDTO,
} from "@/services/api/studies/outputs/variableViews/types";
import type { Area, LinkElement, Simulation } from "../../../../../../types/types";

export const OUTPUT_ITEM_TYPES = ["areas", "links", "synthesis"] as const;
export const DATA_TYPES = ["values", "details", "details-res", "id", "details-STstorage"] as const;
export const FREQUENCIES = ["hourly", "daily", "weekly", "monthly", "annual"] as const;
export const MONTE_CARLO_MODES = ["mc-ind", "mc-all", "variable-per-variable"] as const;

export type OutputItemType = (typeof OUTPUT_ITEM_TYPES)[number];
export type DataType = (typeof DATA_TYPES)[number];
export type Frequency = (typeof FREQUENCIES)[number];
export type MonteCarloMode = (typeof MONTE_CARLO_MODES)[number];

interface Params {
  output: Partial<Simulation> & { id: string; name: string };
  item: (Area & { id: string }) | LinkElement;
  dataType: DataType;
  frequency: Frequency;
  year?: number;
}

export const MAX_YEAR = 99999;

export function createPath(params: Params): string {
  const { output, item, dataType, frequency, year } = params;
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

  return `output/${id}/${mode.toLowerCase()}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${frequency}`;
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

////////////////////////////////////////////////////////////////
// Variable per variable utils
////////////////////////////////////////////////////////////////

/**
 * Builds parameters for variable view API requests based on item type and data type
 *
 * @param itemType - The type of output item (areas, links, or synthesis)
 * @param dataType - The type of data being requested (values, details, details-res, details-STstorage, or id)
 * @param selectedClusterId - The ID of the selected cluster (for cluster-specific data types)
 * @param selectedItemId - The ID of the selected item (area name or link ID)
 * @param selectedItem - The full item object (Area or LinkElement)
 * @param selectedVariable - The name of the variable to retrieve
 * @param frequency - The time frequency for the data (hourly, daily, weekly, monthly, annual)
 * @returns VariableViewParams object configured for the appropriate endpoint
 *
 * @example
 * // For area values
 * buildVariableViewParams("areas", "values", "", "area1", areaObj, "LOAD", "hourly")
 * // Returns: { type: "area", variableName: "LOAD", frequency: "hourly", areaId: "area1" }
 *
 * // For thermal cluster details
 * buildVariableViewParams("areas", "details", "cluster1", "area1", areaObj, "production", "daily")
 * // Returns: { type: "thermal", variableName: "production", frequency: "daily", areaId: "area1", clusterId: "cluster1" }
 *
 * // For links
 * buildVariableViewParams("links", "values", "", "link1", linkObj, "FLOW LIN.", "monthly")
 * // Returns: { type: "link", variableName: "FLOW LIN.", frequency: "monthly", areaFromId: "area1", areaToId: "area2" }
 */
export function buildVariableViewParams(
  itemType: OutputItemType,
  dataType: string,
  selectedClusterId: string,
  selectedItemId: string,
  selectedItem: (Area & { id: string }) | LinkElement,
  selectedVariable: string,
  frequency: Frequency,
): VariableViewParams {
  if (itemType === "areas") {
    // Cluster/storage params
    if (dataType === "details" && selectedClusterId) {
      return {
        type: "thermal",
        variableName: selectedVariable,
        frequency: frequency,
        areaId: selectedItemId,
        clusterId: selectedClusterId,
      };
    }
    if (dataType === "details-res" && selectedClusterId) {
      return {
        type: "renewable",
        variableName: selectedVariable,
        frequency: frequency,
        areaId: selectedItemId,
        clusterId: selectedClusterId,
      };
    }
    if (dataType === "details-STstorage" && selectedClusterId) {
      return {
        type: "st_storage",
        variableName: selectedVariable,
        frequency: frequency,
        areaId: selectedItemId,
        clusterId: selectedClusterId,
      };
    }

    // Area params
    return {
      type: "area",
      variableName: selectedVariable,
      frequency: frequency,
      areaId: selectedItemId,
    };
  }

  // Link params
  return {
    type: "link",
    variableName: selectedVariable,
    frequency: frequency,
    areaFromId: (selectedItem as LinkElement).area1,
    areaToId: (selectedItem as LinkElement).area2,
  };
}

/**
 * Retrieves the first variable for a selected item (area or link)
 *
 * @param variablesMetadata - The metadata containing all variables information, or null if not loaded
 * @param itemType - The type of item (areas, links, or synthesis)
 * @param selectedItemId - The ID of the selected item (area name or link ID in format "area1%area2")
 * @returns The first variable name for the item, or empty string if not found or no variables exist
 *
 * @example
 * // For an area
 * getFirstVariableForItem(metadata, "areas", "area1") // Returns first variable of area1
 *
 * // For a link
 * getFirstVariableForItem(metadata, "links", "area1%area2") // Returns first variable of the link
 */
export function getFirstVariableForItem(
  variablesMetadata: VariablesListDTO | null,
  itemType: OutputItemType,
  selectedItemId: string,
): string {
  if (!variablesMetadata || !selectedItemId) {
    return "";
  }

  const data = variablesMetadata.mcInd;

  if (itemType === "areas") {
    const area = data.areas.find((area) => area.name === selectedItemId);
    return area?.variables[0] || "";
  }

  if (itemType === "links") {
    const link = data.links.find((link) =>
      isLinkMatch(link.area1Name, link.area2Name, selectedItemId),
    );
    return link?.variables[0] || "";
  }

  return "";
}

/**
 * Extracts variables from an area based on the data type
 *
 * @param area - The area containing variables and clusters
 * @param dataType - The type of data to extract (values, details, details-res, details-STstorage)
 * @returns Array of variable names
 */
export function getAreaVariables(area: AreaVariablesDTO, dataType: DataType): string[] {
  switch (dataType) {
    case "values":
      return area.variables;

    case "details":
      return (
        area.thermalClusters?.flatMap((cluster: ThermalClusterVariablesDTO) => cluster.variables) ||
        []
      );

    case "details-res":
      return (
        area.renewableClusters?.flatMap(
          (cluster: RenewableClusterVariablesDTO) => cluster.variables,
        ) || []
      );

    case "details-STstorage":
      return (
        area.shortTermStorages?.flatMap(
          (storage: ShortTermStorageVariablesDTO) => storage.variables,
        ) || []
      );

    default:
      return [];
  }
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
 * Extracts variables based on item type (areas or links)
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param itemType - The type of item (areas or links)
 * @param selectedItemId - The ID of the selected item
 * @param dataType - The type of data to extract
 * @returns Array of variable names
 */
export function getVariables(
  variablesMetadata: VariablesListDTO,
  itemType: OutputItemType,
  selectedItemId: string,
  dataType: DataType,
): string[] {
  const data = variablesMetadata.mcInd;

  if (itemType === "areas") {
    const area = data.areas.find((a) => a.name === selectedItemId);
    return area ? getAreaVariables(area, dataType) : [];
  }

  if (itemType === "links") {
    const link = data.links.find((link) =>
      isLinkMatch(link.area1Name, link.area2Name, selectedItemId),
    );
    return link?.variables || [];
  }

  return [];
}

////////////////////////////////////////////////////////////////
// Cluster utils
////////////////////////////////////////////////////////////////

export interface ClusterOption {
  name: string;
  variables: string[];
}

/**
 * Extracts thermal cluster list for a given area
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @returns Array of thermal clusters with their names and variables
 */
export function getThermalClusters(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
): ClusterOption[] {
  if (!variablesMetadata || !areaId) {
    return [];
  }

  const area = variablesMetadata.mcInd.areas.find((a) => a.name === areaId);
  return area?.thermalClusters || [];
}

/**
 * Extracts renewable cluster list for a given area
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @returns Array of renewable clusters with their names and variables
 */
export function getRenewableClusters(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
): ClusterOption[] {
  if (!variablesMetadata || !areaId) {
    return [];
  }

  const area = variablesMetadata.mcInd.areas.find((a) => a.name === areaId);
  return area?.renewableClusters || [];
}

/**
 * Extracts short-term storage list for a given area
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @returns Array of short-term storages with their names and variables
 */
export function getShortTermStorages(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
): ClusterOption[] {
  if (!variablesMetadata || !areaId) {
    return [];
  }

  const area = variablesMetadata.mcInd.areas.find((a) => a.name === areaId);
  return area?.shortTermStorages || [];
}

/**
 * Gets cluster options based on the data type
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @param dataType - The type of data (details, details-res, details-STstorage)
 * @returns Array of cluster options based on data type
 */
export function getClusters(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
  dataType: DataType,
): ClusterOption[] {
  switch (dataType) {
    case "details":
      return getThermalClusters(variablesMetadata, areaId);
    case "details-res":
      return getRenewableClusters(variablesMetadata, areaId);
    case "details-STstorage":
      return getShortTermStorages(variablesMetadata, areaId);
    default:
      return [];
  }
}

/**
 * Gets the first cluster ID for a given area and data type
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @param dataType - The type of data
 * @returns The first cluster ID, or empty string if not found
 */
export function getFirstClusterId(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
  dataType: DataType,
): string {
  const clusters = getClusters(variablesMetadata, areaId, dataType);
  return clusters[0]?.name || "";
}

/**
 * Gets variables for a specific cluster
 *
 * @param variablesMetadata - The metadata containing all variables information
 * @param areaId - The ID of the area
 * @param dataType - The type of data
 * @param clusterId - The ID of the cluster
 * @returns Array of variable names for the cluster
 */
export function getClusterVariables(
  variablesMetadata: VariablesListDTO | null,
  areaId: string,
  dataType: DataType,
  clusterId: string,
): string[] {
  const clusters = getClusters(variablesMetadata, areaId, dataType);
  const cluster = clusters.find((c) => c.name === clusterId);
  return cluster?.variables || [];
}
