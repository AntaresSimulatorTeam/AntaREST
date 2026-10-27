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

import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import type { StoragesParams } from "@/services/api/studies/areas/storages/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useUpdateStorage({ studyId, areaId }: StoragesParams) {
  const queryClient = useQueryClient();

  const { queryKey: queryListKey } = storageQueries.list(studyId, areaId);

  return useMutation({
    ...storageMutations.update(studyId, areaId),
    onSuccess: async (updatedStorage) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) =>
        old.map((storage) => (storage.id === updatedStorage.id ? updatedStorage : storage)),
      );
    },
  });
}

export default useUpdateStorage;
