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

// UI row for one symmetry, adapted from a `ReservesSymmetries` entry.
// `uiId` and `index` have no API equivalent: they exist for row identity
// (React keys, undo/redo) and display order in the table.
export interface SymmetryRow {
  uiId: string;
  clusterId: string;
  // 1-based, sequential within the cluster.
  index: number;
  reserves: Set<string>;
}

// UI grouping of a cluster's symmetry rows, adapted from a `ReservesSymmetries`
// payload merged against the area's cluster list.
export interface ClusterGroup {
  clusterId: string;
  clusterName: string;
  symmetries: SymmetryRow[];
}
