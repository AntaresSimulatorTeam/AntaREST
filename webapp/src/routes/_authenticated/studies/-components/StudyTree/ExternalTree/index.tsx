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

import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import { getParentPaths } from "@/utils/pathUtils";
import { SimpleTreeView } from "@mui/x-tree-view";
import * as R from "ramda";
import { useCallback, useMemo } from "react";
import ExternalTreeNode from "./ExternalTreeNode";
import { useFolderExplorer } from "./hooks/useFolderExplorer";
import { useStudyTree } from "./hooks/useStudyTree";
import { useWorkspaces } from "./hooks/useWorkspaces";
import type { ExternalTreeProps } from "./types";

function ExternalTree({ studies }: ExternalTreeProps) {
  const dispatch = useAppDispatch();
  // Get current folder filter - allows to display studies in the current folder
  const filters = useAppSelector((state) => getStudyFilters(state), R.T);
  const path = filters.external.path;

  // Fetch workspaces (only in desktop mode)
  const { data: workspaces } = useWorkspaces();
  const workspacesStable = useMemo(() => workspaces ?? [], [workspaces]);

  // Manage folder exploration
  const { explorePath, exploredFolders, itemsLoading } = useFolderExplorer();

  // Manage study tree state
  const { studiesTree, updateTreeWithFolders } = useStudyTree({
    studies,
    workspaces: workspacesStable,
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
      }
    },
    [explorePath, updateTreeWithFolders],
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
      defaultExpandedItems={[...getParentPaths(path), path]}
      defaultSelectedItems={path}
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
