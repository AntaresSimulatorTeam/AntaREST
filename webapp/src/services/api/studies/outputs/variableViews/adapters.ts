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

import type { VariableViewMatrixDTO, VariableViewParams, VariableViewParamsDTO } from "./types";

/**
 * Adapts VariableViewParams to a DTO format suitable for query parameters.
 * Converts camelCase property names to snake_case and structures the data
 * according to the variable type (area, link, thermal, renewable, st_storage).
 *
 * @param params - The variable view parameters to adapt
 * @returns A record of query parameter key-value pairs in DTO format
 */
export function adaptVariableViewParamsToDto(params: VariableViewParams): VariableViewParamsDTO {
  const baseParams = {
    variable_name: params.variableName,
    frequency: params.frequency,
  };

  switch (params.type) {
    case "area":
      return {
        ...baseParams,
        type: "area",
        area_id: params.areaId,
      };
    case "link":
      return {
        ...baseParams,
        type: "link",
        area_from_id: params.areaFromId,
        area_to_id: params.areaToId,
      };
    case "thermal":
      return {
        ...baseParams,
        type: "thermal",
        area_id: params.areaId,
        thermal_id: params.clusterId,
      };
    case "renewable":
      return {
        ...baseParams,
        type: "renewable",
        area_id: params.areaId,
        renewable_id: params.clusterId,
      };
    case "st_storage":
      return {
        ...baseParams,
        type: "st_storage",
        area_id: params.areaId,
        st_storage_id: params.clusterId,
      };
  }
}

/**
 * Sanitizes JSON response containing invalid NaN literals.
 *
 * The backend serializes NaN as literal tokens (e.g., {"value": NaN})
 * using Pydantic's ser_json_inf_nan="constants" configuration. This is invalid JSON
 * and causes JSON.parse() to fail.
 *
 * This function converts these literals to valid JSON strings before parsing:
 * - NaN → "NaN" (later handled by formatGridNumber to display as empty cell)
 *
 * @param response - Raw response data from axios (string or already parsed object)
 * @returns Properly parsed VariableViewMatrixDTO object
 */
export function sanitizeNaNResponse(
  response: string | VariableViewMatrixDTO,
): VariableViewMatrixDTO {
  // If already parsed as an object, return as-is
  if (typeof response === "object") {
    return response;
  }

  // Replace invalid JSON literals with valid JSON strings
  const sanitized = response.replace(/NaN/g, '"NaN"');

  return JSON.parse(sanitized);
}
