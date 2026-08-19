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

import {
  adaptReservesSymmetriesDtoToRows,
  adaptSymmetryRowsToReservesSymmetriesEntry,
  createSymmetryRow,
  reindexSymmetryRows,
} from "@/services/api/studies/areas/reserves/adapters";
import type { ReservesSymmetries, SymmetryRow } from "@/services/api/studies/areas/reserves/types";

// The backend requires at least 2 distinct reserve IDs per symmetry. Enforced
// here (not in the API schema) so a violation can be tied to a specific row.
export const MIN_RESERVES_PER_SYMMETRY = 2;

export interface ClusterGroup {
  clusterId: string;
  clusterName: string;
  symmetries: SymmetryRow[];
}

export interface SymmetryValidationError {
  uiId: string;
  clusterId: string;
  clusterName: string;
  index: number;
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
export function fromApi(
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
export function toApi(groups: readonly ClusterGroup[]): ReservesSymmetries {
  const result: ReservesSymmetries = {};

  for (const group of groups) {
    if (group.symmetries.length > 0) {
      result[group.clusterId] = adaptSymmetryRowsToReservesSymmetriesEntry(group.symmetries);
    }
  }

  return result;
}

/**
 * Appends `count` new, fully unchecked symmetries to the given cluster.
 *
 * @param groups - The current domain model.
 * @param clusterId - The cluster to add symmetries to.
 * @param count - How many symmetries to add.
 * @returns The updated domain model.
 */
export function addSymmetries(
  groups: readonly ClusterGroup[],
  clusterId: string,
  count: number,
): ClusterGroup[] {
  return groups.map((group) => {
    if (group.clusterId !== clusterId) {
      return group;
    }

    const newRows = Array.from({ length: count }, () => createSymmetryRow(clusterId));

    return { ...group, symmetries: reindexSymmetryRows([...group.symmetries, ...newRows]) };
  });
}

/**
 * Removes the given symmetry rows (by UI id, possibly across several
 * clusters) and renumbers the remaining rows of each affected cluster.
 * A cluster left with zero symmetries keeps its group row.
 *
 * @param groups - The current domain model.
 * @param uiIds - UI ids of the rows to remove.
 * @returns The updated domain model.
 */
export function deleteSymmetryRows(
  groups: readonly ClusterGroup[],
  uiIds: ReadonlySet<string>,
): ClusterGroup[] {
  return groups.map((group) => {
    const remaining = group.symmetries.filter((row) => !uiIds.has(row.uiId));

    if (remaining.length === group.symmetries.length) {
      return group;
    }

    return { ...group, symmetries: reindexSymmetryRows(remaining) };
  });
}

/**
 * Inserts an exact copy of the given symmetry row immediately after it, and
 * renumbers subsequent symmetries of the same cluster. No-op if
 * `uiId` doesn't match any row.
 *
 * @param groups - The current domain model.
 * @param uiId - UI id of the row to duplicate.
 * @returns The updated domain model.
 */
export function duplicateSymmetryRow(
  groups: readonly ClusterGroup[],
  uiId: string,
): ClusterGroup[] {
  return groups.map((group) => {
    const index = group.symmetries.findIndex((row) => row.uiId === uiId);

    if (index === -1) {
      return group;
    }

    const duplicate = createSymmetryRow(group.clusterId, group.symmetries[index].reserves);
    const nextSymmetries = [...group.symmetries];
    nextSymmetries.splice(index + 1, 0, duplicate);

    return { ...group, symmetries: reindexSymmetryRows(nextSymmetries) };
  });
}

/**
 * Toggles a single (symmetry, reserve) cell (no exclusivity
 * constraint). No-op if `uiId` doesn't match any row.
 *
 * @param groups - The current domain model.
 * @param uiId - UI id of the symmetry row.
 * @param reserveId - The reserve to check/uncheck.
 * @returns The updated domain model.
 */
export function toggleReserve(
  groups: readonly ClusterGroup[],
  uiId: string,
  reserveId: string,
): ClusterGroup[] {
  return groups.map((group) => {
    const index = group.symmetries.findIndex((row) => row.uiId === uiId);

    if (index === -1) {
      return group;
    }

    const row = group.symmetries[index];
    const nextReserves = new Set(row.reserves);

    if (nextReserves.has(reserveId)) {
      nextReserves.delete(reserveId);
    } else {
      nextReserves.add(reserveId);
    }

    const nextSymmetries = [...group.symmetries];
    nextSymmetries[index] = { ...row, reserves: nextReserves };

    return { ...group, symmetries: nextSymmetries };
  });
}

/**
 * Flags symmetries with fewer than `MIN_RESERVES_PER_SYMMETRY` checked
 * reserves, which the backend would reject on save.
 *
 * @param groups - The current domain model.
 * @returns One entry per invalid symmetry row.
 */
export function validateGroups(groups: readonly ClusterGroup[]): SymmetryValidationError[] {
  const errors: SymmetryValidationError[] = [];

  for (const group of groups) {
    for (const row of group.symmetries) {
      if (row.reserves.size < MIN_RESERVES_PER_SYMMETRY) {
        errors.push({
          uiId: row.uiId,
          clusterId: group.clusterId,
          clusterName: group.clusterName,
          index: row.index,
        });
      }
    }
  }

  return errors;
}
