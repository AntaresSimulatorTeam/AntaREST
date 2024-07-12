import { MRT_AggregationFn } from "material-react-table";
import { ThermalClusterWithCapacity } from "../Thermal/utils";
import { RenewableClusterWithCapacity } from "../Renewables/utils";

export function toCapacityString(
  enabledCapacity: number,
  installedCapacity: number,
) {
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
export const capacityAggregationFn = <
  T extends ThermalClusterWithCapacity | RenewableClusterWithCapacity,
>(): MRT_AggregationFn<T> => {
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

interface BaseCluster {
  name: string;
  group: string;
  unitCount: number;
  nominalCapacity: number;
  enabled: boolean;
}

export type ClusterWithCapacity<T extends BaseCluster> = T & {
  installedCapacity: number;
  enabledCapacity: number;
};

/**
 * Adds the installed and enabled capacity fields to a cluster.
 *
 * @param cluster - The cluster to add the capacity fields to.
 * @returns The cluster with the installed and enabled capacity fields added.
 */
export function addClusterCapacity<T extends BaseCluster>(cluster: T) {
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
