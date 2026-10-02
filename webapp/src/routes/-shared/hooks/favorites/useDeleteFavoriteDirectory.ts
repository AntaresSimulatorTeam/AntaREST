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
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteFavoriteDirectory() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { queryKey: favoritesQueryKey } = directoryQueries.favorites();

  const mutation = useMutation({
    ...directoryMutations.deleteFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const favToDelete = favorites.find((fav) => fav.directoryId === variables.directoryId);

      if (favToDelete) {
        queryClient.setQueryData(favoritesQueryKey, (old) => {
          return old?.filter((fav) => fav.directoryId !== favToDelete.directoryId);
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

export default useDeleteFavoriteDirectory;
