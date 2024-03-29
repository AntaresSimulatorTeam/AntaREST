import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const RENEWABLE_GROUPS = [
  "Wind Onshore",
  "Wind Offshore",
  "Solar Thermal",
  "Solar PV",
  "Solar Rooftop",
  "Other RES 1",
  "Other RES 2",
  "Other RES 3",
  "Other RES 4",
] as const;

export const TS_INTERPRETATION_OPTIONS = [
  "power-generation",
  "production-factor",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

type TimeSeriesInterpretation = (typeof TS_INTERPRETATION_OPTIONS)[number];
type RenewableGroup = (typeof RENEWABLE_GROUPS)[number];

export interface RenewableFormFields {
  name: string;
  group: string;
  tsInterpretation: TimeSeriesInterpretation;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

export interface RenewableCluster {
  id: string;
  name: string;
  group: RenewableGroup;
  tsInterpretation: TimeSeriesInterpretation;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

export interface RenewableClusterWithCapacity extends RenewableCluster {
  installedCapacity: number;
  enabledCapacity: number;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getClustersUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string => `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`;

const getClusterUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string => `${getClustersUrl(studyId, areaId)}/${clusterId}`;

async function makeRequest<T>(
  method: "get" | "post" | "patch" | "delete",
  url: string,
  data?: Partial<RenewableCluster> | { data: Array<Cluster["id"]> },
): Promise<T> {
  const res = await client[method]<T>(url, data);
  return res.data;
}

export async function getRenewableClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): Promise<RenewableCluster[]> {
  return makeRequest<RenewableCluster[]>(
    "get",
    getClustersUrl(studyId, areaId),
  );
}

export async function getRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): Promise<RenewableCluster> {
  return makeRequest<RenewableCluster>(
    "get",
    getClusterUrl(studyId, areaId, clusterId),
  );
}

export async function updateRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<RenewableCluster>,
): Promise<RenewableCluster> {
  return makeRequest<RenewableCluster>(
    "patch",
    getClusterUrl(studyId, areaId, clusterId),
    data,
  );
}

export async function createRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: Partial<RenewableCluster>,
): Promise<RenewableClusterWithCapacity> {
  return makeRequest<RenewableClusterWithCapacity>(
    "post",
    getClustersUrl(studyId, areaId),
    data,
  );
}

export function deleteRenewableClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
): Promise<void> {
  return makeRequest<void>("delete", getClustersUrl(studyId, areaId), {
    data: clusterIds,
  });
}
