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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryMutations } from "@/queries/directories/mutations";
import { directoryQueries } from "@/queries/directories/queries";
import { createOptimisticListItem } from "@/queries/utils";
import type { FavoriteDirectory } from "@/services/api/favorites/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useCreateFavoriteDirectory() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { queryKey: favoritesQueryKey } = directoryQueries.favorites();

  const mutation = useMutation({
    ...directoryMutations.createFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const { directoryId } = variables;
      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const isAlreadyFavorite = favorites.some((fav) => fav.directoryId === directoryId);

      if (!isAlreadyFavorite) {
        const directories = queryClient.getQueryData(directoryQueries.list().queryKey) || [];

        queryClient.setQueryData(favoritesQueryKey, (old = []) => {
          return [
            ...old,
            createOptimisticListItem<FavoriteDirectory>({
              directoryId,
              directoryName: directories.find((dir) => dir.id === directoryId)?.name || directoryId,
            }),
          ];
        });
      }

      return { noMutation: isAlreadyFavorite };
    },
    onError: (error, variables, onMutateResult) => {
      if (onMutateResult?.noMutation) {
        return;
      }

      enqueueErrorSnackbar(t("directory.error.createFavorite"), error);

      queryClient.setQueryData(favoritesQueryKey, (old = []) => {
        return old.filter((fav) => fav.directoryId !== variables.directoryId);
      });
    },
    onSuccess: (newFavorite, _, onMutateResult) => {
      if (onMutateResult?.noMutation) {
        return;
      }

      queryClient.setQueryData(favoritesQueryKey, (old = []) => {
        return old.map((fav) => (fav.directoryId === newFavorite.directoryId ? newFavorite : fav));
      });
    },
  });

  return mutation;
}

export default useCreateFavoriteDirectory;
