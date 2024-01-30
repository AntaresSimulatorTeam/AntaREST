import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const THERMAL_GROUPS = [
  "Gas",
  "Hard Coal",
  "Lignite",
  "Mixed fuel",
  "Nuclear",
  "Oil",
  "Other",
  "Other 2",
  "Other 3",
  "Other 4",
] as const;

export const THERMAL_POLLUTANTS = [
  // For study versions >= 860
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
] as const;

export const TS_GENERATION_OPTIONS = [
  "use global",
  "force no generation",
  "force generation",
] as const;

export const TS_LAW_OPTIONS = ["geometric", "uniform"] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

type ThermalGroup = (typeof THERMAL_GROUPS)[number];
type LocalTSGenerationBehavior = (typeof TS_GENERATION_OPTIONS)[number];
type TimeSeriesLawOption = (typeof TS_LAW_OPTIONS)[number];

type ThermalPollutants = {
  [K in (typeof THERMAL_POLLUTANTS)[number]]: number;
};

export interface ThermalCluster extends ThermalPollutants {
  id: string;
  name: string;
  group: ThermalGroup;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
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
  genTs: LocalTSGenerationBehavior;
  volatilityForced: number;
  volatilityPlanned: number;
  lawForced: TimeSeriesLawOption;
  lawPlanned: TimeSeriesLawOption;
}

export interface ThermalClusterWithCapacity extends ThermalCluster {
  enabledCapacity: number;
  installedCapacity: number;
}

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
): Promise<ThermalClusterWithCapacity> {
  return makeRequest<ThermalClusterWithCapacity>(
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
