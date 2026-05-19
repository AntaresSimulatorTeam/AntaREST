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

import type { QueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useCallback } from "react";
import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import type { Directory } from "@/services/api/directories/types";
import type { DirectoryDestination } from "./types";
import { resolveRedirectDirectoryId } from "./utils";

/**
 * Invalidates and re-reads the directory cache when the destination created new
 * sub-directories. Returns the original list unchanged when no refresh is needed.
 */
export async function refreshDirectoriesIfNeeded(
  queryClient: QueryClient,
  destination: DirectoryDestination,
  directories: Directory[],
): Promise<Directory[]> {
  if (!destination.newSubdirectoriesPath) {
    return directories;
  }

  await queryClient.invalidateQueries({ queryKey: directoryQueries.list().queryKey });

  return queryClient.getQueryData(directoryQueries.list().queryKey) ?? directories;
}

/**
 * Hook returning a callback that points the studies page at a destination directory.
 *
 * Shared by Move and Import dialogs which both navigate to `/studies` after success.
 * The caller is responsible for ensuring `directories` is fresh (invalidating the
 * directory cache when new sub-directories were created).
 */
export function useRedirectToDestination() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  return useCallback(
    (destination: DirectoryDestination, directories: Directory[]) => {
      const directoryId = resolveRedirectDirectoryId(destination, directories);

      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: {
            directoryId,
            directoryIds: directoryId ? getDescendantIds(directoryId, directories) : null,
          },
        }),
      );

      navigate({ to: "/studies" });
    },
    [dispatch, navigate],
  );
}
