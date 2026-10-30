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

import type { Storage, StorageParams } from "@/services/api/studies/areas/storages/types";
import type { UseSuspenseQueryResult } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { O } from "ts-toolbelt";
import useStorages from "../../-hooks/useStorages";

interface UseStorageParams<TData = Storage> extends StorageParams {
  select?: (data: Storage) => TData;
}

function useStorage(params: Omit<UseStorageParams, "select">): UseSuspenseQueryResult<Storage>;

function useStorage<TData>(
  params: O.Required<UseStorageParams<TData>, "select">,
): UseSuspenseQueryResult<TData>;

function useStorage<TData>({ studyId, areaId, storageId, select }: UseStorageParams<TData>) {
  const { t } = useTranslation();

  const getStorage = useCallback(
    (storages: Storage[]) => {
      return storages.find(({ id }) => id === storageId);
    },
    [storageId],
  );

  const { data: storage, ...restResult } = useStorages({
    studyId,
    areaId,
    select: getStorage,
  });

  const selection = useMemo(() => {
    if (!storage || !select) {
      return;
    }
    return select(storage);
  }, [select, storage]);

  if (!storageId) {
    throw new Error(t("route.noParameter", { param: "storageId" }));
  }

  if (!storage) {
    throw new Error(t("study.modeling.storages.notFound", { id: storageId }));
  }

  return {
    ...restResult,
    data: select ? selection : storage,
  };
}

export default useStorage;
