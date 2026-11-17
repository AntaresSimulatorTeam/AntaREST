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

import usePrevious from "react-use/lib/usePrevious";
import * as R from "ramda";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters, getStudyFolderRevealRequest } from "@/redux/selectors";
import { getParentPaths } from "@/utils/pathUtils";
import { SimpleTreeView } from "@mui/x-tree-view";
import { useCallback, useMemo, useState } from "react";
import useRevealTreeItem from "../hooks/useRevealTreeItem";
import ExternalTreeNode from "./ExternalTreeNode";
import { useFolderExplorer } from "./hooks/useFolderExplorer";
import usePrepareFolderReveal from "./hooks/usePrepareFolderReveal";
import { useStudyTree } from "./hooks/useStudyTree";
import { useWorkspaces } from "./hooks/useWorkspaces";
import type { ExternalTreeProps } from "./types";

function ExternalTree({ studies }: ExternalTreeProps) {
  const dispatch = useAppDispatch();
  const path = useAppSelector((state) => getStudyFilters(state).external.path);
  const isActive = useAppSelector((state) => getStudyFilters(state).activeTree === "external");
  const revealRequest = useAppSelector(getStudyFolderRevealRequest);
  const request = revealRequest?.tree === "external" ? revealRequest : null;
  const requestId = request?.requestId;
  const requestedPath = request?.path;
  const requestedWorkspace = requestedPath?.split("/")[1];

  const workspaceQuery = useWorkspaces({
    enabled: !!request && !studies.some((study) => study.workspace === requestedWorkspace),
  });
  const { data: workspaces } = workspaceQuery;
  const workspacesStable = useMemo(() => workspaces ?? [], [workspaces]);

  const { explorePath, markPathExplored, exploredFolders, itemsLoading } = useFolderExplorer();

  const { studiesTree, updateTreeWithFolders } = useStudyTree({
    studies,
    workspaces: workspacesStable,
  });

  const prevPath = usePrevious(path);
  const prevRequestId = usePrevious(requestId);
  const [expandedItems, setExpandedItems] = useState<string[]>(() =>
    [...getParentPaths(path), path].filter(Boolean),
  );

  // Links outside the tree must also expand the selected folder's ancestors.
  if (prevPath !== path || (requestId && prevRequestId !== requestId)) {
    const required = [...getParentPaths(path), path].filter(Boolean);
    const missing = R.difference(required, expandedItems);

    if (missing.length > 0) {
      setExpandedItems([...expandedItems, ...missing]);
    }
  }

  const workspaceReady =
    studiesTree.children.some((node) => node.path === `/${requestedWorkspace}`) ||
    (workspaceQuery.isFetched && !workspaceQuery.isFetching);

  const isReadyToReveal = usePrepareFolderReveal({
    request,
    studiesTree,
    workspaceReady,
    workspaceError: workspaceQuery.error,
    explorePath,
    markPathExplored,
    updateTreeWithFolders,
  });

  const { treeRef, apiRef } = useRevealTreeItem({
    requestId,
    itemId: path,
    ready: isReadyToReveal,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  /**
   * Handles folder expansion in the tree.
   * Fetches subfolders when a folder is expanded for the first time.
   *
   * We handle both expand events and click events because:
   * - Click events aren't triggered when clicking the expand arrow
   * - Expand events aren't triggered when an item has no subfolders
   *   (but we still want to apply the filter on clicked folders)
   */
  const handleItemExpansionToggle = useCallback(
    async (_event: React.SyntheticEvent | null, itemId: string, isExpanded: boolean) => {
      if (!isExpanded) {
        return;
      }

      const folders = await explorePath(itemId);

      if (folders) {
        updateTreeWithFolders(folders, itemId);
        markPathExplored(itemId);
      }
    },
    [explorePath, markPathExplored, updateTreeWithFolders],
  );

  const handleItemClick = (_event: React.MouseEvent, itemId: string) => {
    dispatch(
      updateStudyFilters({
        activeTree: "external",
        external: { path: itemId },
      }),
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SimpleTreeView
      ref={treeRef}
      apiRef={apiRef}
      expandedItems={expandedItems}
      onExpandedItemsChange={(_event, itemIds) => setExpandedItems(itemIds)}
      selectedItems={isActive ? path : ""}
      onItemExpansionToggle={handleItemExpansionToggle}
      onItemClick={handleItemClick}
    >
      {studiesTree.children.map((child) => (
        <ExternalTreeNode
          key={child.path}
          node={child}
          itemsLoading={itemsLoading}
          exploredFolders={exploredFolders}
        />
      ))}
    </SimpleTreeView>
  );
}

export default ExternalTree;
