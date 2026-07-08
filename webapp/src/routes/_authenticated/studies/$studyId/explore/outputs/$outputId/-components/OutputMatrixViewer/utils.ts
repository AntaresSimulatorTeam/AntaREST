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

import { Column } from "@/components/Matrix/shared/constants";
import type { EnhancedGridColumn } from "@/components/Matrix/shared/types";
import type { Output } from "@/services/api/studies/outputs/types";
import type { VariableViewParams } from "@/services/api/studies/outputs/variableViews/types";
import { isAreaOrDistrict, isLink, type DataType, type Frequency, type Item } from "../../-utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface ColumnsInfo {
  variables: string[];
  units: string[];
  stats: string[];
}

interface CreateOutputDataPathParams {
  output: Output;
  item: Item;
  dataType: DataType;
  frequency: Frequency;
  year?: number;
}

interface BuildVariableViewParamsParams {
  item: Item;
  dataType: DataType;
  frequency: Frequency;
  clusterId: string;
  variable: string;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const DATE_GRID_COLUMN = {
  id: "date",
  title: "Date",
  type: Column.DateTime,
  editable: false,
} as const satisfies EnhancedGridColumn;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function createOutputDataPath({
  output,
  item,
  dataType,
  frequency,
  year,
}: CreateOutputDataPathParams): string {
  const { id, mode = "economy" } = output;
  const isYearPeriod = year && year > 0;
  const periodFolder = isYearPeriod
    ? `mc-ind/${Math.min(year, output.nbYears).toString().padStart(5, "0")}`
    : "mc-all";
  const itemType = isLink(item) ? "links" : "areas";
  const itemFolder = isLink(item) ? `${item.area1}/${item.area2}` : item.id;

  return `output/${id}/${mode.toLowerCase()}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${frequency}`;
}

/**
 * Check if the given data type is a cluster data type.
 * Note: Short-term storages are considered as clusters in this context.
 *
 * @param dataType - The data type to check.
 * @returns True if the data type is a cluster data type, false otherwise.
 */
export function isClusterDataType(
  dataType: DataType,
): dataType is "details" | "details-res" | "details-STstorage" {
  return (
    // Thermal clusters
    dataType === "details" ||
    // Renewable clusters
    dataType === "details-res" ||
    // Short-term storages
    dataType === "details-STstorage"
  );
}

/**
 * Builds parameters for variable view API requests based on item type and data type.
 *
 * @param params - The parameters for building the variable view request.
 * @param params.item  - The selected item (area, district, or link).
 * @param params.dataType - The type of data being requested.
 * @param params.frequency - The time frequency for the data.
 * @param params.clusterId - The ID of the selected cluster (for cluster-specific data types).
 * @param params.variable - The name of the variable to retrieve.
 * @returns VariableViewParams object configured for the appropriate endpoint.
 */
export function buildVariableViewParams({
  item,
  dataType,
  frequency,
  clusterId,
  variable,
}: BuildVariableViewParamsParams): VariableViewParams {
  if (isAreaOrDistrict(item)) {
    // Cluster params
    if (isClusterDataType(dataType)) {
      const typeByDataType = {
        details: "thermal",
        "details-res": "renewable",
        "details-STstorage": "st_storage",
      } as const;

      return {
        type: typeByDataType[dataType],
        variableName: variable,
        frequency,
        areaId: item.id,
        clusterId,
      };
    }

    // Area params
    return {
      type: "area",
      variableName: variable,
      frequency,
      areaId: item.id,
    };
  }

  // Link params
  return {
    type: "link",
    variableName: variable,
    frequency,
    areaFromId: item.area1,
    areaToId: item.area2,
  };
}
