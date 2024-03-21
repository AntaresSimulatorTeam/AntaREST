import { MRT_AggregationFn } from "material-react-table";
import { ThermalClusterWithCapacity } from "../Thermal/utils";
import { RenewableClusterWithCapacity } from "../Renewables/utils";

/**
 * Custom aggregation function summing the values of each row,
 * to display enabled and installed capacity in the same cell.
 * @param colHeader - the column header
 * @param rows - the column rows to aggregate
 * @returns a string with the sum of enabled and installed capacity.
 * @example "100/200"
 * @see https://www.material-react-table.com/docs/guides/aggregation-and-grouping#custom-aggregation-functions
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

    return `${Math.floor(enabledCapacitySum)} / ${Math.floor(
      installedCapacitySum,
    )}`;
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
