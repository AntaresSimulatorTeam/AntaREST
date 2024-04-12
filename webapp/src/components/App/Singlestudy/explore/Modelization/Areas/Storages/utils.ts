import { StudyMetadata, Area } from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";
import type { PartialExceptFor } from "../../../../../../../utils/tsUtils";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const STORAGE_GROUPS = [
  "PSP_open",
  "PSP_closed",
  "Pondage",
  "Battery",
  "Other1",
  "Other2",
  "Other3",
  "Other4",
  "Other5",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type StorageGroup = (typeof STORAGE_GROUPS)[number];

export interface Storage {
  id: string;
  name: string;
  group: StorageGroup;
  injectionNominalCapacity: number;
  withdrawalNominalCapacity: number;
  reservoirCapacity: number;
  efficiency: number;
  initialLevel: number;
  initialLevelOptim: boolean;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getStoragesUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string => `/v1/studies/${studyId}/areas/${areaId}/storages`;

const getStorageUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
): string => `${getStoragesUrl(studyId, areaId)}/${storageId}`;

async function makeRequest<T>(
  method: "get" | "post" | "patch" | "delete",
  url: string,
  data?: Partial<Storage> | { data: Array<Storage["id"]> } | null,
  params?: Record<string, string>,
): Promise<T> {
  const res = await client[method]<T>(url, data, params && { params });
  return res.data;
}

export async function getStorages(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): Promise<Storage[]> {
  return makeRequest<Storage[]>("get", getStoragesUrl(studyId, areaId));
}

export async function getStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
): Promise<Storage> {
  return makeRequest<Storage>("get", getStorageUrl(studyId, areaId, storageId));
}

export async function updateStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  data: Partial<Storage>,
): Promise<Storage> {
  return makeRequest<Storage>(
    "patch",
    getStorageUrl(studyId, areaId, storageId),
    data,
  );
}

export function createStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<Storage, "name">,
) {
  return makeRequest<Storage>("post", getStoragesUrl(studyId, areaId), data);
}

export function duplicateStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: Storage["id"],
  newName: Storage["name"],
) {
  return makeRequest<Storage>(
    "post",
    `/v1/studies/${studyId}/areas/${areaId}/storages/${sourceClusterId}`,
    null,
    { newName },
  );
}

export function deleteStorages(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageIds: Array<Storage["id"]>,
): Promise<void> {
  return makeRequest<void>("delete", getStoragesUrl(studyId, areaId), {
    data: storageIds,
  });
}
