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

import type { Options } from "@/components/fieldEditors/SelectFE";
import { isQueryListItemOptimistic } from "@/queries/utils";
import type { MRT_AggregationFn } from "material-react-table";

interface BaseCluster {
  id: string;
  name: string;
  group: string | null;
  unitCount: number;
  nominalCapacity: number;
  enabled: boolean;
}

export type ClusterWithCapacity<T extends BaseCluster = BaseCluster> = T & {
  installedCapacity: number;
  enabledCapacity: number;
};

export function toCapacityString(enabledCapacity: number, installedCapacity: number) {
  return `${Math.round(enabledCapacity)} / ${Math.round(installedCapacity)}`;
}

/**
 * Custom aggregation function summing the values of each row,
 * to display enabled and installed capacity in the same cell. This function is
 * designed for use with Material React Table's custom aggregation feature, allowing
 * the combination of enabled and installed capacities into a single cell.
 *
 * @returns A string representing the sum of enabled and installed capacity in the format "enabled/installed".
 * @example
 * Assuming an aggregation of rows where enabled capacities sum to 100 and installed capacities sum to 200
 * "100/200"
 *
 * @see https://www.material-react-table.com/docs/guides/aggregation-and-grouping#custom-aggregation-functions for more information on custom aggregation functions in Material React Table.
 */
export const capacityAggregationFn = <T extends ClusterWithCapacity>(): MRT_AggregationFn<T> => {
  return (columnId, leafRows) => {
    const { enabledCapacitySum, installedCapacitySum } = leafRows.reduce(
      (acc, row) => {
        acc.enabledCapacitySum += row.original.enabledCapacity;
        acc.installedCapacitySum += row.original.installedCapacity;

        return acc;
      },
      { enabledCapacitySum: 0, installedCapacitySum: 0 },
    );

    return toCapacityString(enabledCapacitySum, installedCapacitySum);
  };
};

/**
 * Adds the installed and enabled capacity fields to a cluster.
 *
 * @param cluster - The cluster to add the capacity fields to.
 * @returns The cluster with the installed and enabled capacity fields added.
 */
export function addClusterCapacity<T extends BaseCluster>(cluster: T): ClusterWithCapacity<T> {
  const { unitCount, nominalCapacity, enabled } = cluster;
  const installedCapacity = unitCount * nominalCapacity;
  const enabledCapacity = enabled ? installedCapacity : 0;
  return { ...cluster, installedCapacity, enabledCapacity };
}

/**
 * Gets the totals for unit count, installed capacity, and enabled capacity
 * for the specified clusters.
 *
 * @param clusters - The clusters to get the totals for.
 * @returns An object containing the totals.
 */
export function getClustersWithCapacityTotals<T extends BaseCluster>(
  clusters: Array<ClusterWithCapacity<T>>,
) {
  return clusters.reduce(
    (acc, { unitCount, installedCapacity, enabledCapacity }) => {
      acc.totalUnitCount += unitCount;
      acc.totalInstalledCapacity += installedCapacity;
      acc.totalEnabledCapacity += enabledCapacity;
      return acc;
    },
    {
      totalUnitCount: 0,
      totalInstalledCapacity: 0,
      totalEnabledCapacity: 0,
    },
  );
}

/**
 * Transforms a list of base clusters into enriched data for display.
 *
 * Each cluster is augmented with its capacity information, and aggregated
 * totals are computed across all clusters.
 *
 * Intended for use as the `select` option of a Tanstack Query hook.
 *
 * @see addClusterCapacity
 * @see getClustersWithCapacityTotals
 *
 * @param clusters - The base clusters to select data for.
 * @returns An object containing the clusters with capacity and their totals.
 */
export function selectClustersData<T extends BaseCluster>(clusters: T[]) {
  const clustersWithCapacity = clusters.map(addClusterCapacity);

  return {
    clustersWithCapacity,
    totals: getClustersWithCapacityTotals(clustersWithCapacity),
  };
}

/**
 * Transforms a list of clusters into options suitable for a select field.
 *
 * Optimistic clusters will be marked as disabled in the select options.
 *
 * @param clusters - The clusters to transform.
 * @returns An array of options for the select field.
 */
export function clustersToOptions<T extends BaseCluster>(clusters: T[]): Options<T["id"]> {
  return clusters.map((cluster) => ({
    label: cluster.name,
    value: cluster.id,
    group: cluster.group ?? undefined,
    disabled: isQueryListItemOptimistic(cluster),
  }));
}
