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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FolderDTO, WorkspaceDTO } from "@/queries/explorer/schemas";
import storage, { StorageKey } from "@/services/utils/localStorage";
import type { StudyMetadata } from "@/types/types";
import type { ExternalTreeNodeMetadata } from "../types";
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
  const [studiesTree, setStudiesTree] = useState<ExternalTreeNodeMetadata>(() =>
    buildExternalTree(studies),
  );
  const [subFolders, setSubFolders] = useState<FolderDTO[]>(
    () => storage.getItem(StorageKey.StudyTreeFolders) || [],
  );

  // Use ref to track the current subFolders value without causing re-renders
  const subFoldersRef = useRef(subFolders);
  subFoldersRef.current = subFolders;

  const updateTreeWithFolders = useCallback(
    (newFolders: FolderDTO[], parentPath: string) => {
      // Keep folders from other parent paths
      const otherSubfolders = R.filter(
        (folder) => folder.parentPath !== parentPath,
        subFoldersRef.current,
      );

      // Filter new folders to only include unscanned studies
      const filteredNewFolders = R.filter(
        (folder) => isUnscannedStudy(studies, folder),
        newFolders,
      );

      // Combine and update state
      const nextSubfolders = [...filteredNewFolders, ...otherSubfolders];
      setSubFolders(nextSubfolders);

      // Update tree
      const nextStudyTree = insertIfNotExist(
        buildExternalTree(studies),
        workspaces,
        nextSubfolders,
      );
      setStudiesTree(nextStudyTree);

      // Persist to local storage
      storage.setItem(StorageKey.StudyTreeFolders, nextSubfolders);

      return nextStudyTree;
    },
    [studies, workspaces],
  );

  // Memoize filtered subFolders to prevent unnecessary recalculations
  const filteredSubFolders = useMemo(
    () => R.filter((folder) => isUnscannedStudy(studies, folder), subFolders),
    [studies, subFolders],
  );

  // Rebuild tree when studies, workspaces, or filtered subFolders change
  useEffect(() => {
    const nextStudyTree = insertIfNotExist(
      buildExternalTree(studies),
      workspaces,
      filteredSubFolders,
    );
    setStudiesTree(nextStudyTree);
  }, [studies, workspaces, filteredSubFolders]);

  return {
    studiesTree,
    subFolders,
    updateTreeWithFolders,
  };
}
