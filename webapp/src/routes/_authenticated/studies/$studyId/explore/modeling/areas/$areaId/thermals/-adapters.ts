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

import { nameToId } from "@/services/utils";
import type { ThermalCluster } from "@/services/api/studies/areas/thermals/types";

/**
 * Uses canonical IDs for links and empty groups for the existing table and form.
 *
 * @param cluster - The complete API cluster.
 * @returns The cluster with a normalized ID and string group for UI consumers.
 */
export function adaptThermalClusterToView(cluster: ThermalCluster) {
  return { ...cluster, id: nameToId(cluster.id), group: cluster.group ?? "" };
}
