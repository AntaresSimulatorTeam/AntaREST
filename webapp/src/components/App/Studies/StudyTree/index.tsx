/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { StudyTreeNode } from ".././utils";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../../redux/selectors";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../../redux/ducks/studies";
import TreeItemEnhanced from "../../../common/TreeItemEnhanced";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../../utils/pathUtils";
import * as R from "ramda";
import { useState } from "react";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useUpdateEffectOnce from "@/hooks/useUpdateEffectOnce";
import { fetchAndInsertSubfolders, fetchAndInsertWorkspaces } from "./utils";
import { useTranslation } from "react-i18next";
import { toError } from "@/utils/fnUtils";

function StudyTree() {
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();

  // Initialize folders once we have the tree
  // we use useUpdateEffectOnce because at first render initialStudiesTree isn't initialized
  useUpdateEffectOnce(() => {
    // be carefull to pass initialStudiesTree and not studiesTree at rootNode parameter
    // otherwise we'll lose the default workspace
    updateTree("root", initialStudiesTree, initialStudiesTree);
  }, [initialStudiesTree]);

  /**
   * This function is called at the initialization of the component and when the user clicks on a folder.
   *
   * The study tree is built from the studies in the database. There's a scan process that run on the server
   * to update continuously the studies in the database.
   *
   * However this process can take a long time, and the user shouldn't wait for hours before he can see a study he knows is already uploaded.
   *
   * Instead of relying on the scan process to update the tree, we'll allow the user to walk into the tree and run a scan process only when he needs to.
   *
   * To enable this, we'll fetch the subfolders of a folder when the user clicks on it using the explorer API.
   *
   * @param itemId - The id of the item clicked
   * @param rootNode - The root node of the tree
   * @param selectedNode - The node of the item clicked
   */
  async function updateTree(
    itemId: string,
    rootNode: StudyTreeNode,
    selectedNode: StudyTreeNode,
  ) {
    // Bug fix : this function used to take only the itemId and the selectedNode, and we used to initialize treeAfterWorkspacesUpdate
    // with the studiesTree closure, referencing directly the state, like this : treeAfterWorkspacesUpdate = studiesTree;
    // The thing is at the first render studiesTree was empty.
    // This made updateTree override studiesTree with an empty tree during the first call. This caused a bug where we didn't see the default
    // workspace in the UI, as it was overridden by an empty tree at start and then the get workspaces api never returns the default workspace.
    // Now we don't use the closure anymore, we pass the root tree as a parameter. Thus at the first call of updateTree, we pass initialStudiesTree.
    // You may think why we don't just capture initialStudiesTree then, it's because in the following call we need to pass studiesTree.
    let treeAfterWorkspacesUpdate = rootNode;
    let chidrenPaths = selectedNode.children.map(
      (child) => `root/${child.path}`,
    );
    // If the user clicks on the root folder, we fetch the workspaces and insert them.
    // Then we fetch the direct subfolders of the workspaces.
    if (itemId === "root") {
      try {
        treeAfterWorkspacesUpdate = await fetchAndInsertWorkspaces(rootNode);
        chidrenPaths = treeAfterWorkspacesUpdate.children.map(
          (child) => `root${child.path}`,
        );
      } catch (error) {
        enqueueErrorSnackbar(
          "studies.tree.error.failToFetchWorkspace",
          toError(error),
        );
      }
    } else {
      // If the user clicks on a folder, we add the path of the clicked folder to the list of paths to fetch.
      // as well as the path of the children of the clicked folder.
      // If we don't fetch the subfolders of the children then we won't know if they're themselves folders, which we need
      // to know to display the little arrow next to the subfolder.
      // On the other hand, if we fetch only the subfolders of the children, then we won't fetch their "siblings" folder
      // if one of them is added.
      chidrenPaths = [selectedNode.path].concat(chidrenPaths);
    }

    const [treeAfterChildrenUpdate, failedPath] =
      await fetchAndInsertSubfolders(chidrenPaths, treeAfterWorkspacesUpdate);
    if (failedPath.length > 0) {
      enqueueErrorSnackbar(
        t("studies.tree.error.failToFetchFolder", {
          path: failedPath.join(" "),
          interpolation: { escapeValue: false },
        }),
        t("studies.tree.error.detailsInConsole"),
      );
    }
    setStudiesTree(treeAfterChildrenUpdate);
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = async (
    itemId: string,
    studyTreeNode: StudyTreeNode,
  ) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    updateTree(itemId, studiesTree, studyTreeNode);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const buildTree = (children: StudyTreeNode[], parentId?: string) => {
    return children.map((child) => {
      const id = parentId ? `${parentId}/${child.name}` : child.name;

      return (
        <TreeItemEnhanced
          key={id}
          itemId={id}
          label={child.name}
          onClick={() => handleTreeItemClick(id, child)}
        >
          {buildTree(child.children, id)}
        </TreeItemEnhanced>
      );
    });
  };

  return (
    <SimpleTreeView
      defaultExpandedItems={[...getParentPaths(folder), folder]}
      defaultSelectedItems={folder}
      sx={{
        flexGrow: 1,
        height: 0,
        width: 1,
        py: 1,
        overflowY: "auto",
        overflowX: "hidden",
      }}
    >
      {buildTree([studiesTree])}
    </SimpleTreeView>
  );
}

export default StudyTree;
