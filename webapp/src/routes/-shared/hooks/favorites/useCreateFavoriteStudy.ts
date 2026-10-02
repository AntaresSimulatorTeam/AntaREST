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
import { createOptimisticListItem } from "@/queries/utils";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesById } from "@/redux/selectors";
import type { FavoriteStudy } from "@/services/api/favorites/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useCreateFavoriteStudy() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const studiesById = useAppSelector(getStudiesById);

  const { queryKey: favoritesQueryKey } = studyQueries.favorites();

  const mutation = useMutation({
    ...studyMutations.createFavorite(),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: favoritesQueryKey });

      const { studyId } = variables;
      const favorites = queryClient.getQueryData(favoritesQueryKey) || [];
      const isAlreadyFavorite = favorites.some((fav) => fav.studyId === studyId);

      if (!isAlreadyFavorite) {
        queryClient.setQueryData(favoritesQueryKey, (old = []) => {
          return [
            ...old,
            createOptimisticListItem<FavoriteStudy>({
              studyId,
              studyName: studiesById[studyId]?.name || studyId,
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

      enqueueErrorSnackbar(t("study.error.createFavorite"), error);

      queryClient.setQueryData(favoritesQueryKey, (old) => {
        return old?.filter((fav) => fav.studyId !== variables.studyId);
      });
    },
    onSuccess: (newFavorite, _, onMutateResult) => {
      if (onMutateResult?.noMutation) {
        return;
      }

      queryClient.setQueryData(favoritesQueryKey, (old) => {
        return old?.map((fav) => (fav.studyId === newFavorite.studyId ? newFavorite : fav));
      });
    },
  });

  return mutation;
}

export default useCreateFavoriteStudy;
