/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import * as storageApi from "@/services/api/studies/areas/storages";
import type { StorageGroup, StorageResponse } from "@/services/api/studies/areas/storages/types";
import type { Area } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import * as RA from "ramda-adjunct";
import { adaptStorageToView } from "./-adapters";
import type { Study } from "@/services/api/studies/types";

// TODO(PR2): remove compatibility exports and wrappers once consumers use the Storage data layer.
export { STORAGE_GROUPS } from "@/services/api/studies/areas/storages/constants";
export type { StorageGroup } from "@/services/api/studies/areas/storages/types";

export type Storage<LegacyGroup extends boolean = false> = Omit<
  Required<StorageResponse>,
  "group"
> & {
  group: LegacyGroup extends true ? StorageGroup : string;
};

export type FormalizedStorage = ReturnType<typeof adaptStorageToView>;

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

export async function getStorages(studyId: Study["id"], areaId: Area["name"]) {
  const storages = await storageApi.getStorages({ studyId, areaId });
  return storages.map(adaptStorageToView);
}

export async function getStorage(
  studyId: Study["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
) {
  const storage = await storageApi.getStorage({ studyId, areaId, storageId });
  return adaptStorageToView(storage);
}

export async function updateStorage(
  studyId: Study["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  data: Partial<Storage>,
) {
  const storage = await storageApi.updateStorage({ studyId, areaId, storageId, values: data });
  return adaptStorageToView(storage);
}

export async function createStorage(
  studyId: Study["id"],
  areaId: Area["name"],
  data: PartialExceptFor<Storage, "name">,
) {
  const storage = await storageApi.createStorage({ studyId, areaId, values: data });
  return adaptStorageToView(storage);
}

export async function duplicateStorage(
  studyId: Study["id"],
  areaId: Area["name"],
  sourceClusterId: Storage["id"],
  newName: Storage["name"],
) {
  const storage = await storageApi.duplicateStorage({
    studyId,
    areaId,
    storageId: sourceClusterId,
    newName,
  });
  return adaptStorageToView(storage);
}

export function deleteStorages(
  studyId: Study["id"],
  areaId: Area["name"],
  storageIds: Array<Storage["id"]>,
) {
  return storageApi.deleteStorages({ studyId, areaId, storageIds });
}

export function convertRatioToPercentage<T extends Partial<Storage>>(storage: T): T {
  const values = { ...storage };

  // Convert to percentage ([0-1] -> [0-100])
  if (RA.isNumber(values.efficiency)) {
    values.efficiency *= 100;
  }
  if (RA.isNumber(values.initialLevel)) {
    values.initialLevel *= 100;
  }
  if (RA.isNumber(values.efficiencyWithdrawal)) {
    values.efficiencyWithdrawal *= 100;
  }

  return values;
}

export function convertPercentageToRatio(storage: Partial<Storage>): Partial<Storage> {
  const values = { ...storage };

  // Convert to ratio ([0-100] -> [0-1])
  if (RA.isNumber(values.efficiency)) {
    values.efficiency /= 100;
  }
  if (RA.isNumber(values.initialLevel)) {
    values.initialLevel /= 100;
  }
  if (RA.isNumber(values.efficiencyWithdrawal)) {
    values.efficiencyWithdrawal /= 100;
  }

  return values;
}
