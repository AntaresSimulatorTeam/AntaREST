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

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getStorages(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
) {
  const res = await client.get<Storage[]>(getStoragesUrl(studyId, areaId));
  return res.data;
}

export async function getStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
) {
  const res = await client.get<Storage>(
    getStorageUrl(studyId, areaId, storageId),
  );
  return res.data;
}

export async function updateStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  data: Partial<Storage>,
) {
  const res = await client.patch<Storage>(
    getStorageUrl(studyId, areaId, storageId),
    data,
  );
  return res.data;
}

export async function createStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<Storage, "name">,
) {
  const res = await client.post<Storage>(getStoragesUrl(studyId, areaId), data);
  return res.data;
}

export async function duplicateStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: Storage["id"],
  newName: Storage["name"],
) {
  const res = await client.post<Storage>(
    `/v1/studies/${studyId}/areas/${areaId}/storages/${sourceClusterId}`,
    null,
    { params: { newName } },
  );
  return res.data;
}

export async function deleteStorages(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageIds: Array<Storage["id"]>,
) {
  await client.delete(getStoragesUrl(studyId, areaId), { data: storageIds });
}
