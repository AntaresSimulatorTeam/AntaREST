/* eslint-disable camelcase */
import { MRT_AggregationFn } from "material-react-table";
import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum ThermalClusterGroup {
  Gas = "Gas",
  HardCoal = "Hard Coal",
  Lignite = "Lignite",
  MixedFuel = "Mixed fuel",
  Nuclear = "Nuclear",
  Oil = "Oil",
  Other = "Other",
  Other2 = "Other 2",
  Other3 = "Other 3",
  Other4 = "Other 4",
}

enum TimeSeriesGenerationOption {
  UseGlobal = "use global parameter",
  ForceNoGeneration = "force no generation",
  ForceGeneration = "force generation",
}

enum LawOption {
  Geometric = "geometric",
  Uniform = "uniform",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface ThermalClusterPollutants {
  // For study versions >= 860
  co2: number;
  so2: number;
  nh3: number;
  nox: number;
  nmvoc: number;
  pm25: number;
  pm5: number;
  pm10: number;
  op1: number;
  op2: number;
  op3: number;
  op4: number;
  op5: number;
}

export interface ThermalCluster extends ThermalClusterPollutants {
  id: string;
  name: string;
  group: string;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
  installedCapacity: number;
  enabledCapacity: number;
  mustRun: boolean;
  minStablePower: number;
  spinning: number;
  minUpTime: number;
  minDownTime: number;
  marginalCost: number;
  fixedCost: number;
  startupCost: number;
  marketBidCost: number;
  spreadCost: number;
  genTs: TimeSeriesGenerationOption;
  volatilityForced: number;
  volatilityPlanned: number;
  lawForced: LawOption;
  lawPlanned: LawOption;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const CLUSTER_GROUP_OPTIONS = Object.values(ThermalClusterGroup);
export const TS_GENERATION_OPTIONS = Object.values(TimeSeriesGenerationOption);
export const TS_LAW_OPTIONS = Object.values(LawOption);
export const POLLUTANT_NAMES: Array<keyof ThermalClusterPollutants> = [
  "co2",
  "so2",
  "nh3",
  "nox",
  "nmvoc",
  "pm25",
  "pm5",
  "pm10",
  "op1",
  "op2",
  "op3",
  "op4",
  "op5",
];

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getClustersUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string => `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`;

const getClusterUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string => `${getClustersUrl(studyId, areaId)}/${clusterId}`;

async function makeRequest<T>(
  method: "get" | "post" | "patch" | "delete",
  url: string,
  data?: Partial<ThermalCluster> | { data: Array<Cluster["id"]> },
): Promise<T> {
  const res = await client[method]<T>(url, data);
  return res.data;
}

export async function getThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): Promise<ThermalCluster[]> {
  return makeRequest<ThermalCluster[]>("get", getClustersUrl(studyId, areaId));
}

export async function getThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): Promise<ThermalCluster> {
  return makeRequest<ThermalCluster>(
    "get",
    getClusterUrl(studyId, areaId, clusterId),
  );
}

export async function updateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<ThermalCluster>,
): Promise<ThermalCluster> {
  return makeRequest<ThermalCluster>(
    "patch",
    getClusterUrl(studyId, areaId, clusterId),
    data,
  );
}

export async function createThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: Partial<ThermalCluster>,
): Promise<ThermalCluster> {
  return makeRequest<ThermalCluster>(
    "post",
    getClustersUrl(studyId, areaId),
    data,
  );
}

export function deleteThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
): Promise<void> {
  return makeRequest<void>("delete", getClustersUrl(studyId, areaId), {
    data: clusterIds,
  });
}

/**
 * Custom aggregation function summing the values of each row,
 * to display enabled and installed capacity in the same cell.
 * @param colHeader - the column header
 * @param rows - the column rows to aggregate
 * @returns a string with the sum of enabled and installed capacity.
 * @example "100/200"
 * @see https://www.material-react-table.com/docs/guides/aggregation-and-grouping#custom-aggregation-functions
 */
export const capacityAggregationFn: MRT_AggregationFn<ThermalCluster> = (
  colHeader,
  rows,
) => {
  const { enabledCapacitySum, installedCapacitySum } = rows.reduce(
    (
      acc: { enabledCapacitySum: number; installedCapacitySum: number },
      row,
    ) => {
      acc.enabledCapacitySum += row.original.enabledCapacity ?? 0;
      acc.installedCapacitySum += row.original.installedCapacity ?? 0;
      return acc;
    },
    { enabledCapacitySum: 0, installedCapacitySum: 0 },
  );

  return `${enabledCapacitySum} / ${installedCapacitySum}`;
};
