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
import { studyMutations } from "@/queries/studies/mutations";
import { studyQueries } from "@/queries/studies/queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteFavoriteStudy() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const { queryKey: favoritesQueryKey } = studyQueries.favorites();

  const mutate = useMutation({
    ...studyMutations.deleteFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const favToDelete = favorites.find((fav) => fav.studyId === variables.studyId);

      if (favToDelete) {
        queryClient.setQueryData(favoritesQueryKey, (old = []) => {
          return old.filter((fav) => fav.studyId !== favToDelete.studyId);
        });
      }

      return favToDelete;
    },
    onError: (error, _, favToDelete) => {
      if (!favToDelete) {
        return;
      }

      // TODO  key
      enqueueErrorSnackbar(t("study.favorite.delete.error"), error);

      queryClient.setQueryData(favoritesQueryKey, (old = []) => {
        return [...old, favToDelete];
      });
    },
  });

  return mutate;
}

export default useDeleteFavoriteStudy;
