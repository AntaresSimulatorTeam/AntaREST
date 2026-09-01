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

import type { ClusterGroup, ReservesSymmetries, SymmetryRow } from "./types";

export function createSymmetryRow(
  clusterId: string,
  reserveIds: Iterable<string> = [],
): SymmetryRow {
  return {
    uiId: crypto.randomUUID(),
    clusterId,
    index: 0, // Overwritten by `reindexSymmetryRows`.
    reserves: new Set(reserveIds),
  };
}

export function reindexSymmetryRows(rows: SymmetryRow[]): SymmetryRow[] {
  return rows.map((row, i) => (row.index === i + 1 ? row : { ...row, index: i + 1 }));
}

/**
 * Converts one cluster's raw symmetries entry from the API payload into UI rows.
 *
 * @param clusterId - The cluster the symmetries belong to.
 * @param symmetries - The cluster's entry from the API payload, if any.
 * @returns One row per symmetry, indexed from 1.
 */
export function adaptReservesSymmetriesDtoToRows(
  clusterId: string,
  symmetries: string[][] = [],
): SymmetryRow[] {
  return reindexSymmetryRows(
    symmetries.map((reserveIds) => createSymmetryRow(clusterId, reserveIds)),
  );
}

/**
 * Serializes a cluster's UI rows back to the API payload's array-of-arrays shape.
 *
 * @param rows - The cluster's current symmetry rows.
 * @returns One entry per row, in order.
 */
export function adaptSymmetryRowsToReservesSymmetriesEntry(
  rows: readonly SymmetryRow[],
): string[][] {
  return rows.map((row) => [...row.reserves]);
}

/**
 * Builds the UI domain model from the API payload, merged against the full
 * cluster list of the area so every cluster gets a row group, even with no
 * symmetries.
 *
 * @param clusters - All clusters of the area.
 * @param data - The API's symmetries payload.
 * @returns The domain model, one group per cluster.
 */
export function adaptReservesSymmetriesDtoToClusterGroups(
  clusters: ReadonlyArray<{ id: string; name: string }>,
  data: ReservesSymmetries,
): ClusterGroup[] {
  return clusters.map((cluster) => ({
    clusterId: cluster.id,
    clusterName: cluster.name,
    symmetries: adaptReservesSymmetriesDtoToRows(cluster.id, data[cluster.id]),
  }));
}

/**
 * Serializes the UI domain model back to the API payload. Clusters with no
 * symmetries are omitted (equivalent to an absent/empty entry).
 *
 * @param groups - The current domain model.
 * @returns The full API payload to PUT.
 */
export function adaptClusterGroupsToReservesSymmetriesDto(
  groups: readonly ClusterGroup[],
): ReservesSymmetries {
  const result: ReservesSymmetries = {};

  for (const group of groups) {
    if (group.symmetries.length > 0) {
      result[group.clusterId] = adaptSymmetryRowsToReservesSymmetriesEntry(group.symmetries);
    }
  }

  return result;
}
