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

import * as R from "ramda";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { FolderDTO, WorkspaceDTO } from "@/queries/explorer/schemas";
import storage, { StorageKey } from "@/services/utils/localStorage";
import type { StudyMetadata } from "@/types/types";
import { buildExternalTree, insertIfNotExist, isUnscannedStudy } from "../utils";

interface UseStudyTreeOptions {
  studies: StudyMetadata[];
  workspaces: WorkspaceDTO[];
}

/**
 * Hook to manage the study tree state, including local storage synchronization
 * and tree rebuilding when studies or workspaces change.
 *
 * @param options - Configuration options
 * @param options.studies - Studies to include in the tree
 * @param options.workspaces - Workspaces to include in the tree
 * @returns Study tree state and management functions
 */
export function useStudyTree({ studies, workspaces }: UseStudyTreeOptions) {
  const [subFolders, setSubFolders] = useState<FolderDTO[]>(
    () => storage.getItem(StorageKey.StudyTreeFolders) || [],
  );

  const filterUnscannedFolders = useCallback(
    (folders: FolderDTO[]): FolderDTO[] =>
      R.filter((folder) => isUnscannedStudy(studies, folder), folders),
    [studies],
  );

  const updateTreeWithFolders = useCallback(
    (newFolders: FolderDTO[], parentPath: string) => {
      const filteredNewFolders = filterUnscannedFolders(newFolders);

      // Several ancestors can finish loading before React renders their updates.
      setSubFolders((previous) => [
        ...filteredNewFolders,
        ...previous.filter((folder) => folder.parentPath !== parentPath),
      ]);
    },
    [filterUnscannedFolders],
  );

  const studiesTree = useMemo(
    () =>
      insertIfNotExist(buildExternalTree(studies), workspaces, filterUnscannedFolders(subFolders)),
    [studies, workspaces, filterUnscannedFolders, subFolders],
  );

  useEffect(() => {
    storage.setItem(StorageKey.StudyTreeFolders, subFolders);
  }, [subFolders]);

  return {
    studiesTree,
    subFolders,
    updateTreeWithFolders,
  };
}
