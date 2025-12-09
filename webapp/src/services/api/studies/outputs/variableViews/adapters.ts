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

import type { VariableViewParams } from "./types";

/**
 * Adapts VariableViewParams to a DTO format suitable for query parameters.
 * Converts camelCase property names to snake_case and structures the data
 * according to the variable type (area, link, thermal, renewable, st_storage).
 *
 * @param params - The variable view parameters to adapt
 * @returns A record of query parameter key-value pairs in DTO format
 */
export function adaptVariableViewParamsToDto(params: VariableViewParams): Record<string, string> {
  const queryParams: Record<string, string> = {
    type: params.type,
    variable_name: params.variableName,
    frequency: params.frequency,
  };

  switch (params.type) {
    case "area":
      queryParams.area_id = params.areaId;
      break;
    case "link":
      queryParams.area_from_id = params.areaFromId;
      queryParams.area_to_id = params.areaToId;
      break;
    case "thermal":
      queryParams.area_id = params.areaId;
      queryParams.thermal_id = params.clusterId;
      break;
    case "renewable":
      queryParams.area_id = params.areaId;
      queryParams.renewable_id = params.clusterId;
      break;
    case "st_storage":
      queryParams.area_id = params.areaId;
      queryParams.storage_id = params.clusterId;
      break;
  }

  return queryParams;
}
