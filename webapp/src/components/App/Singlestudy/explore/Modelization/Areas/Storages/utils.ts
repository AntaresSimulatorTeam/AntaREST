import { StudyMetadata, Area } from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

const StorageGroup = {
  PspOpen: "PSP_open",
  PspClosed: "PSP_closed",
  Pondage: "Pondage",
  Battery: "Battery",
  Other1: "Other1",
  Other2: "Other2",
  Other3: "Other3",
  Other4: "Other4",
  Other5: "Other5",
} as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type StorageGroup = (typeof StorageGroup)[keyof typeof StorageGroup];

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
// Constants
////////////////////////////////////////////////////////////////

export const STORAGE_GROUPS = [...Object.values(StorageGroup)];

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
  data?: Partial<Storage> | { data: Array<Storage["id"]> },
): Promise<T> {
  const res = await client[method]<T>(url, data);
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

export async function createStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: Partial<Storage>,
): Promise<Storage> {
  return makeRequest<Storage>("post", getStoragesUrl(studyId, areaId), data);
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
