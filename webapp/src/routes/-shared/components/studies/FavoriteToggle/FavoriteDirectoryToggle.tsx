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

import { directoryQueries } from "@/queries/directories/queries";
import useCreateFavoriteDirectory from "@/routes/-shared/hooks/favorites/useCreateFavoriteDirectory";
import useDeleteFavoriteDirectory from "@/routes/-shared/hooks/favorites/useDeleteFavoriteDirectory";
import type { Directory } from "@/services/api/directories/types";
import type { FavoriteDirectory } from "@/services/api/favorites/types";
import { useIsMutating, useSuspenseQuery } from "@tanstack/react-query";
import * as RA from "ramda-adjunct";
import { useCallback } from "react";
import FavoriteButton, { type FavoriteButtonProps } from "./FavoriteButton";

interface Props extends Omit<FavoriteButtonProps, "isFavorite" | "onClick"> {
  directoryId: Directory["id"];
}

function FavoriteDirectoryToggle({ directoryId, ...rest }: Props) {
  const createFavorite = useCreateFavoriteDirectory();
  const deleteFavorite = useDeleteFavoriteDirectory();

  const selectIsFavorite = useCallback(
    (favorites: FavoriteDirectory[]) => favorites.some((fav) => fav.directoryId === directoryId),
    [directoryId],
  );

  const { data: isFavorite } = useSuspenseQuery({
    ...directoryQueries.favorites(),
    select: selectIsFavorite,
  });

  // Indicates whether a favorite mutation (create or delete) is currently in progress for this directory
  const isMutating =
    useIsMutating({
      mutationKey: directoryQueries.favorites().queryKey,
      predicate: ({ state: { variables } }) => {
        return (
          RA.isPlainObj(variables) &&
          "directoryId" in variables &&
          variables.directoryId === directoryId
        );
      },
    }) !== 0;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    if (isFavorite) {
      deleteFavorite.mutate({ directoryId });
    } else {
      createFavorite.mutate({ directoryId });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FavoriteButton isFavorite={isFavorite} onClick={handleClick} loading={isMutating} {...rest} />
  );
}

export default FavoriteDirectoryToggle;
