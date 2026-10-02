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
import { externalDirectoryQueries } from "@/queries/externalDirectories/queries";
import { studyQueries } from "@/queries/studies/queries";
import useCreateFavoriteStudy from "@/routes/-shared/hooks/favorites/useCreateFavoriteStudy";
import type {
  FavoriteDirectory,
  FavoriteExternalDirectory,
  FavoriteStudy,
} from "@/services/api/favorites/types";
import { sortByName } from "@/services/utils";
import storage from "@/services/utils/localStorage";
import { getLastPathSegment, joinPaths } from "@/utils/pathUtils";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMount } from "react-use";
import type { Favorite } from "./types";

function normalizeAndSortFavorites(
  favorites: FavoriteStudy[] | FavoriteDirectory[] | FavoriteExternalDirectory[],
) {
  const normalized = favorites.map((fav): Favorite => {
    if ("directoryId" in fav) {
      return {
        id: `directory-${fav.directoryId}`,
        name: fav.directoryName,
        type: "directory",
        original: fav,
      };
    }

    if ("workspace" in fav) {
      const absolutePath = joinPaths("/", fav.workspace, fav.path);

      return {
        id: `external-directory-${absolutePath}`,
        name: getLastPathSegment(fav.path),
        type: "externalDirectory",
        absolutePath,
        original: fav,
      };
    }

    return {
      id: `study-${fav.studyId}`,
      name: fav.studyName,
      type: "study",
      original: fav,
    };
  });

  return sortByName(normalized);
}

function useFavorites() {
  const createStudyFavorite = useCreateFavoriteStudy();

  // Workaround to migrate favorites stored in localStorage to the new backend system (since v2.30.0).
  // It can be removed after a certain period of time when we are confident that most users have migrated.
  useMount(() => {
    const oldFavorites = storage.getItem("studies.favorites");
    storage.removeItem("studies.favorites");

    if (Array.isArray(oldFavorites)) {
      oldFavorites.forEach((value) => {
        if (typeof value === "string") {
          createStudyFavorite.mutate({ studyId: value });
        }
      });
    }
  });

  const { data: favoriteStudies } = useSuspenseQuery({
    ...studyQueries.favorites(),
    select: normalizeAndSortFavorites,
  });

  const { data: favoriteDirectories } = useSuspenseQuery({
    ...directoryQueries.favorites(),
    select: normalizeAndSortFavorites,
  });

  const { data: favoriteExternalDirectories } = useSuspenseQuery({
    ...externalDirectoryQueries.favorites(),
    select: normalizeAndSortFavorites,
  });

  return [...favoriteStudies, ...favoriteDirectories, ...favoriteExternalDirectories];
}

export default useFavorites;
