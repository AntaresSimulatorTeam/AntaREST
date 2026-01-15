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

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { directoryKeys } from "@/queries/directories/keys";
import { directoryMutations } from "@/queries/directories/mutations";
import type { Directory } from "@/services/api/directories/types";

interface UseDeleteDirectoryOptions {
  onSuccess?: () => void;
}

export function useDeleteDirectory(options?: UseDeleteDirectoryOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    ...directoryMutations.delete(),
    onMutate: async (directoryId) => {
      await queryClient.cancelQueries({ queryKey: directoryKeys.all });

      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      if (previousDirectories) {
        const filteredDirectories = previousDirectories.filter((dir) => dir.id !== directoryId);

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), filteredDirectories);
      }

      return { previousDirectories };
    },
    onError: (_err, _directoryId, context) => {
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: directoryKeys.all });
      options?.onSuccess?.();
    },
  });
}
