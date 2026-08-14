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
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteFavoriteExternalDirectory() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { queryKey: favoritesQueryKey } = externalDirectoryQueries.favorites();

  const mutation = useMutation({
    ...externalDirectoryMutations.deleteFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const favToDelete = favorites.find(
        (fav) => fav.workspace === variables.workspace && fav.path === variables.path,
      );

      if (favToDelete) {
        queryClient.setQueryData(favoritesQueryKey, (old) => {
          return old?.filter(
            (fav) => fav.workspace !== favToDelete.workspace || fav.path !== favToDelete.path,
          );
        });
      }

      return favToDelete;
    },
    onError: (error, _, favToDelete) => {
      if (!favToDelete) {
        return;
      }

      enqueueErrorSnackbar(t("directory.error.deleteFavorite"), error);

      queryClient.setQueryData(favoritesQueryKey, (old = []) => {
        return [...old, favToDelete];
      });
    },
  });

  return mutation;
}

export default useDeleteFavoriteExternalDirectory;
