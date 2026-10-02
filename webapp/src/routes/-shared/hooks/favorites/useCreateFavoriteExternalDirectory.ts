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
import { externalDirectoryMutations } from "@/queries/externalDirectories/mutations";
import { externalDirectoryQueries } from "@/queries/externalDirectories/queries";
import { createOptimisticListItem } from "@/queries/utils";
import type { FavoriteExternalDirectory } from "@/services/api/favorites/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useCreateFavoriteExternalDirectory() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { queryKey: favoritesQueryKey } = externalDirectoryQueries.favorites();

  const mutation = useMutation({
    ...externalDirectoryMutations.createFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const { workspace, path } = variables;
      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const isAlreadyFavorite = favorites.some(
        (fav) => fav.workspace === workspace && fav.path === path,
      );

      if (!isAlreadyFavorite) {
        queryClient.setQueryData(favoritesQueryKey, (old = []) => {
          return [
            ...old,
            createOptimisticListItem<FavoriteExternalDirectory>({
              workspace,
              path,
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
        return old.filter(
          (fav) => fav.workspace !== variables.workspace || fav.path !== variables.path,
        );
      });
    },
    onSuccess: (newFavorite, _, onMutateResult) => {
      if (onMutateResult?.noMutation) {
        return;
      }

      queryClient.setQueryData(favoritesQueryKey, (old = []) => {
        return old.map((fav) =>
          fav.workspace === newFavorite.workspace && fav.path === newFavorite.path
            ? newFavorite
            : fav,
        );
      });
    },
  });

  return mutation;
}

export default useCreateFavoriteExternalDirectory;
