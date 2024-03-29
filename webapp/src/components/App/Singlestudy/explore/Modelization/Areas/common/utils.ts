import { DependencyList, useMemo } from "react";
import * as R from "ramda";
import { MRT_AggregationFn } from "material-react-table";
import { StudyMetadata } from "../../../../../../../common/types";
import { editStudy } from "../../../../../../../services/api/study";
import { ThermalClusterWithCapacity } from "../Thermal/utils";
import { RenewableClusterWithCapacity } from "../Renewables/utils";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import { UsePromiseResponse } from "../../../../../../../hooks/usePromise";

export const saveField = R.curry(
  (
    studyId: StudyMetadata["id"],
    path: string,
    data: Record<string, unknown>,
  ): Promise<void> => {
    return editStudy(data, studyId, path);
  },
);

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
  return (_colHeader, rows) => {
    const { enabledCapacitySum, installedCapacitySum } = rows.reduce(
      (acc, row) => {
        acc.enabledCapacitySum += row.original.enabledCapacity ?? 0;
        acc.installedCapacitySum += row.original.installedCapacity ?? 0;
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

type ClusterWithCapacity<T extends BaseCluster> = T & {
  installedCapacity: number;
  enabledCapacity: number;
};

interface UseClusterDataWithCapacityReturn<T extends BaseCluster> {
  clusters: UsePromiseResponse<T[]>;
  clustersWithCapacity: Array<ClusterWithCapacity<T>>;
  totalUnitCount: number;
  totalInstalledCapacity: number;
  totalEnabledCapacity: number;
}

export const useClusterDataWithCapacity = <T extends BaseCluster>(
  fetchFn: () => Promise<T[]>,
  errorMessage: string,
  deps: DependencyList,
): UseClusterDataWithCapacityReturn<T> => {
  const clusters: UsePromiseResponse<T[]> = usePromiseWithSnackbarError(
    fetchFn,
    {
      errorMessage,
      deps,
    },
  );

  const clustersWithCapacity: Array<ClusterWithCapacity<T>> = useMemo(
    () =>
      clusters.data?.map((cluster) => {
        const { unitCount, nominalCapacity, enabled } = cluster;
        const installedCapacity = unitCount * nominalCapacity;
        const enabledCapacity = enabled ? installedCapacity : 0;
        return { ...cluster, installedCapacity, enabledCapacity };
      }) || [],
    [clusters.data],
  );

  const { totalUnitCount, totalInstalledCapacity, totalEnabledCapacity } =
    useMemo(() => {
      return clustersWithCapacity.reduce(
        (acc, { unitCount, nominalCapacity, enabled }) => {
          acc.totalUnitCount += unitCount;
          acc.totalInstalledCapacity += unitCount * nominalCapacity;
          acc.totalEnabledCapacity += enabled ? unitCount * nominalCapacity : 0;
          return acc;
        },
        {
          totalUnitCount: 0,
          totalInstalledCapacity: 0,
          totalEnabledCapacity: 0,
        },
      );
    }, [clustersWithCapacity]);

  return {
    clusters,
    clustersWithCapacity,
    totalUnitCount: Math.floor(totalUnitCount),
    totalInstalledCapacity: Math.floor(totalInstalledCapacity),
    totalEnabledCapacity: Math.floor(totalEnabledCapacity),
  };
};
