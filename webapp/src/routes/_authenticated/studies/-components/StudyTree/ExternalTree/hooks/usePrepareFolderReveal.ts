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
import type { FolderDTO } from "@/queries/explorer/schemas";
import { finishStudyFolderReveal, type StudyFolderRevealRequest } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { getParentPaths } from "@/utils/pathUtils";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLatest } from "react-use";
import type { ExternalTreeNodeMetadata } from "../types";
import { findNodeByPath, insertFoldersIfNotExist } from "../utils";

interface Options {
  request: Extract<StudyFolderRevealRequest, { tree: "external" }> | null;
  studiesTree: ExternalTreeNodeMetadata;
  workspaceReady: boolean;
  workspaceError: Error | null;
  exploredFolders: readonly string[];
  explorePath: (path: string) => Promise<FolderDTO[] | null>;
  markPathExplored: (path: string) => void;
  updateTreeWithFolders: (folders: FolderDTO[], parentPath: string) => void;
}

export function usePrepareFolderReveal({
  request,
  studiesTree,
  workspaceReady,
  workspaceError,
  exploredFolders,
  explorePath,
  markPathExplored,
  updateTreeWithFolders,
}: Options): boolean {
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [preparedRequestId, setPreparedRequestId] = useState<string>();
  const requestId = request?.requestId;
  const requestedPath = request?.path;

  // Use current callbacks after each await without restarting for every tree update.
  const revealContext = useLatest({
    studiesTree,
    explorePath,
    markPathExplored,
    exploredFolders,
    updateTreeWithFolders,
    workspaceError,
  });

  // A favorite can request a reveal before the explorer mounts.
  useEffect(() => {
    if (!requestId || !requestedPath || !workspaceReady) {
      return;
    }

    let cancelled = false;

    const reportMissingFolder = () => {
      enqueueErrorSnackbar(
        t("studies.tree.error.failToFetchFolder", {
          path: requestedPath,
          interpolation: { escapeValue: false },
        }),
        revealContext.current.workspaceError ?? requestedPath,
      );
      dispatch(finishStudyFolderReveal(requestId));
    };

    const prepareFolder = async () => {
      let tree = revealContext.current.studiesTree;
      const requiredPaths = [...getParentPaths(requestedPath), requestedPath].filter(Boolean);

      for (const [index, itemPath] of requiredPaths.entries()) {
        if (cancelled) {
          return;
        }

        const node = findNodeByPath(tree, itemPath);

        if (!node || node.isScannedStudy || node.isStudyFolder) {
          reportMissingFolder();

          return;
        }

        const nextPath = requiredPaths[index + 1];
        const needsChildren = nextPath
          ? !findNodeByPath(tree, nextPath)
          : !revealContext.current.exploredFolders.includes(itemPath);

        if (needsChildren) {
          const folders = await revealContext.current.explorePath(itemPath);

          if (cancelled) {
            return;
          }

          if (!folders) {
            dispatch(finishStudyFolderReveal(requestId));

            return;
          }

          revealContext.current.updateTreeWithFolders(folders, itemPath);
          revealContext.current.markPathExplored(itemPath);
          tree = insertFoldersIfNotExist(tree, folders);
        }
      }

      setPreparedRequestId(requestId);
    };

    void prepareFolder();

    return () => {
      cancelled = true;
    };
  }, [requestId, requestedPath, workspaceReady, revealContext, dispatch, enqueueErrorSnackbar, t]);

  return requestId !== undefined && preparedRequestId === requestId;
}
