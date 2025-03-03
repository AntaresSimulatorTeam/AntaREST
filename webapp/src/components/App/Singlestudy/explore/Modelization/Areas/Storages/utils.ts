/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type { StudyMetadata, Area } from "../../../../../../../types/types";
import client from "../../../../../../../services/api/client";
import type { PartialExceptFor } from "../../../../../../../utils/tsUtils";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const STORAGE_GROUPS = [
  "psp_open",
  "psp_closed",
  "pondage",
  "battery",
  "other1",
  "other2",
  "other3",
  "other4",
  "other5",
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
  // Since v8.8
  enabled: boolean;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function getStoragesTotals(storages: Storage[]) {
  return storages.reduce(
    (acc, { withdrawalNominalCapacity, injectionNominalCapacity }) => {
      acc.totalWithdrawalNominalCapacity += withdrawalNominalCapacity;
      acc.totalInjectionNominalCapacity += injectionNominalCapacity;
      return acc;
    },
    {
      totalWithdrawalNominalCapacity: 0,
      totalInjectionNominalCapacity: 0,
    },
  );
}

const getStoragesUrl = (studyId: StudyMetadata["id"], areaId: Area["name"]): string =>
  `/v1/studies/${studyId}/areas/${areaId}/storages`;

const getStorageUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
): string => `${getStoragesUrl(studyId, areaId)}/${storageId}`;

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getStorages(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  const res = await client.get<Storage[]>(getStoragesUrl(studyId, areaId));
  return res.data;
}

export async function getStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
) {
  const res = await client.get<Storage>(getStorageUrl(studyId, areaId, storageId));
  return res.data;
}

export async function updateStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  data: Partial<Storage>,
) {
  const res = await client.patch<Storage>(getStorageUrl(studyId, areaId, storageId), data);
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
