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

import client from "../../../../../../../services/api/client";
import type { Area, StudyMetadata } from "../../../../../../../types/types";
import type { ExcludeNullFromProps, PartialExceptFor } from "../../../../../../../utils/tsUtils";

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

export interface Storage<LegacyGroup extends boolean = false> {
  id: string;
  name: string;
  group: LegacyGroup extends true ? StorageGroup : string; // Before v9.2 => StorageGroup, since v9.2 => string
  injectionNominalCapacity: number;
  withdrawalNominalCapacity: number;
  reservoirCapacity: number;
  efficiency: number;
  initialLevel: number;
  initialLevelOptim: boolean;
  // Since v8.8
  enabled: boolean | null;
  // Since v9.2
  efficiencyWithdrawal: number | null;
  penalizeVariationInjection: boolean | null;
  penalizeVariationWithdrawal: boolean | null;
}

export type FormalizedStorage = ExcludeNullFromProps<Storage>;

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

/**
 * Formalizes a storage object by ensuring all properties are defined.
 * Using condition with the study version doesn't allow TypeScript
 * to infer properties types.
 *
 * @param storage - Storage object to formalize.
 * @returns Formalized storage object with all properties defined.
 */
function formalizeStorage(storage: Storage): FormalizedStorage {
  return {
    ...storage,
    enabled: storage.enabled ?? false,
    efficiencyWithdrawal: storage.efficiencyWithdrawal ?? -1,
    penalizeVariationInjection: storage.penalizeVariationInjection ?? false,
    penalizeVariationWithdrawal: storage.penalizeVariationWithdrawal ?? false,
  };
}

export async function getStorages(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  const res = await client.get<Storage[]>(getStoragesUrl(studyId, areaId));
  return res.data.map(formalizeStorage);
}

export async function getStorage(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
) {
  const res = await client.get<Storage>(getStorageUrl(studyId, areaId, storageId));
  return formalizeStorage(res.data);
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
  return formalizeStorage(res.data);
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
  return formalizeStorage(res.data);
}

export async function deleteStorages(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageIds: Array<Storage["id"]>,
) {
  await client.delete(getStoragesUrl(studyId, areaId), { data: storageIds });
}
