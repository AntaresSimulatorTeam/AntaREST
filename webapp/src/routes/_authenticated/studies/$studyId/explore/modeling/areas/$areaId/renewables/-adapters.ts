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

import type { RenewableCluster } from "@/services/api/studies/areas/renewables/types";

/**
 * Represents an absent API group as an empty group for the existing table and form.
 *
 * @param cluster - The complete API cluster.
 * @returns The cluster with a string group for UI consumers.
 */
export function adaptRenewableClusterToView(cluster: RenewableCluster) {
  return { ...cluster, group: cluster.group ?? "" };
}
