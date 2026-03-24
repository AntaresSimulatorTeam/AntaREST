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

import { studyQueries } from "@/queries/studies/queries";
import useCreateFavoriteStudy from "@/routes/-shared/hooks/useCreateFavoriteStudy";
import useDeleteFavoriteStudy from "@/routes/-shared/hooks/useDeleteFavoriteStudy";
import type { FavoriteStudy } from "@/services/api/favorites/types";
import type { StudyMetadata } from "@/types/types";
import { useIsMutating, useSuspenseQuery } from "@tanstack/react-query";
import * as RA from "ramda-adjunct";
import { useCallback } from "react";
import FavoriteButton, { type FavoriteButtonProps } from "./FavoriteButton";
interface Props {
  studyId: StudyMetadata["id"];
  edge?: FavoriteButtonProps["edge"];
  tooltipPlacement?: FavoriteButtonProps["tooltipPlacement"];
}

function FavoriteStudyToggle({ studyId, edge, tooltipPlacement }: Props) {
  const createFavorite = useCreateFavoriteStudy();
  const deleteFavorite = useDeleteFavoriteStudy();

  const selectIsFavorite = useCallback(
    (favorites: FavoriteStudy[]) => favorites.some((fav) => fav.studyId === studyId),
    [studyId],
  );

  const { data: isFavorite } = useSuspenseQuery({
    ...studyQueries.favorites(),
    select: selectIsFavorite,
  });

  // Indicates whether a favorite mutation (create or delete) is currently in progress for this study
  const isMutating =
    useIsMutating({
      mutationKey: studyQueries.favorites().queryKey,
      predicate: ({ state: { variables } }) => {
        return RA.isPlainObj(variables) && "studyId" in variables && variables.studyId === studyId;
      },
    }) !== 0;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    if (isFavorite) {
      deleteFavorite.mutate({ studyId });
    } else {
      createFavorite.mutate({ studyId });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FavoriteButton
      isFavorite={isFavorite}
      onClick={handleClick}
      edge={edge}
      tooltipPlacement={tooltipPlacement}
      loading={isMutating}
    />
  );
}

export default FavoriteStudyToggle;
