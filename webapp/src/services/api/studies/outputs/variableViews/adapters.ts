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

export function buildVariableViewQueryParams(params: VariableViewParams): Record<string, string> {
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
    case "thermal_cluster":
    case "renewable_cluster":
    case "short_term_storage":
      queryParams.area_id = params.areaId;
      queryParams.cluster_id = params.clusterId;
      break;
  }

  return queryParams;
}
