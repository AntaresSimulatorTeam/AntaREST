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

import { externalDirectoryQueries } from "@/queries/externalDirectories/queries";
import useCreateFavoriteExternalDirectory from "@/routes/-shared/hooks/favorites/useCreateFavoriteExternalDirectory";
import useDeleteFavoriteExternalDirectory from "@/routes/-shared/hooks/favorites/useDeleteFavoriteExternalDirectory";
import { favoriteExternalDirectorySchema } from "@/services/api/favorites/schemas";
import type { FavoriteExternalDirectory } from "@/services/api/favorites/types";
import { useIsMutating, useSuspenseQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import FavoriteButton, { type FavoriteButtonProps } from "./FavoriteButton";

interface Props extends Omit<FavoriteButtonProps, "isFavorite" | "onClick"> {
  workspace: string;
  path: string;
}

function FavoriteExternalDirectoryToggle({ workspace, path, ...rest }: Props) {
  const createFavorite = useCreateFavoriteExternalDirectory();
  const deleteFavorite = useDeleteFavoriteExternalDirectory();

  const selectIsFavorite = useCallback(
    (favorites: FavoriteExternalDirectory[]) =>
      favorites.some((fav) => fav.workspace === workspace && fav.path === path),
    [workspace, path],
  );

  const { data: isFavorite } = useSuspenseQuery({
    ...externalDirectoryQueries.favorites(),
    select: selectIsFavorite,
  });

  // Indicates whether a favorite mutation (create or delete) is currently in progress for this directory
  const isMutating =
    useIsMutating({
      mutationKey: externalDirectoryQueries.favorites().queryKey,
      predicate: ({ state: { variables } }) => {
        const result = favoriteExternalDirectorySchema.safeParse(variables);
        if (result.success) {
          return result.data.workspace === workspace && result.data.path === path;
        }
        return false;
      },
    }) !== 0;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    if (isFavorite) {
      deleteFavorite.mutate({ workspace, path });
    } else {
      createFavorite.mutate({ workspace, path });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FavoriteButton isFavorite={isFavorite} onClick={handleClick} loading={isMutating} {...rest} />
  );
}

export default FavoriteExternalDirectoryToggle;
