/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type { NonStudyFolderDTO } from "./types";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../../redux/selectors";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../../redux/ducks/studies";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../../utils/pathUtils";
import * as R from "ramda";
import React, { useState } from "react";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { fetchSubfolders, insertFoldersIfNotExist } from "./utils";
import { useTranslation } from "react-i18next";
import StudyTreeNodeComponent from "./StudyTreeNode";
import { DEFAULT_WORKSPACE_PREFIX, ROOT_FOLDER_NAME } from "@/components/common/utils/constants";
import { useUpdateEffect } from "react-use";

function StudyTree() {
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  const [subFolders, setSubFolders] = useState<NonStudyFolderDTO[]>([]);
  const [itemsLoading, setItemsLoading] = useState<string[]>([]);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();

  useUpdateEffect(() => {
    const nextStudiesTree = insertFoldersIfNotExist(initialStudiesTree, subFolders);
    setStudiesTree(nextStudiesTree);
  }, [initialStudiesTree]);

  /**
   * This function is called when the user clicks on a folder.
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
   * @param itemId - The id of the item clicked, which is its path
   */
  async function updateTree(itemId: string) {
    if (itemId.startsWith(DEFAULT_WORKSPACE_PREFIX)) {
      // we don't update the tree if the user clicks on the default workspace
      // api doesn't allow to fetch the subfolders of the default workspace
      return;
    }
    // If the user clicks on the root folder, we don't update the tree,
    // there're no subfolders under the root only workspaces.
    if (itemId === ROOT_FOLDER_NAME) {
      return;
    }
    // usefull flag to display "loading..." message
    setItemsLoading([...itemsLoading, itemId]);
    // fetch subfolders and inesrt them to the tree
    try {
      const newSubFolders = await fetchSubfolders(itemId);
      // use union to prioritize new subfolders
      const nextSubfolders = R.unionWith(R.eqBy(R.prop("path")), newSubFolders, subFolders);
      setSubFolders(nextSubfolders);
      const nextStudiesTree = insertFoldersIfNotExist(studiesTree, nextSubfolders);
      setStudiesTree(nextStudiesTree);
    } catch {
      enqueueErrorSnackbar(
        t("studies.tree.error.failToFetchFolder", {
          path: itemId,
          interpolation: { escapeValue: false },
        }),
        "",
      );
    }
    setItemsLoading(itemsLoading.filter((e) => e !== itemId));
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  // we need to handle both the expand event and the onClick event
  // because the onClick isn't triggered when user click on arrow
  // Also the expanse event isn't triggered when the item doesn't have any subfolder
  // but we stil want to apply the filter on the clicked folder
  const handleItemExpansionToggle = async (
    event: React.SyntheticEvent<Element, Event>,
    itemId: string,
    isExpanded: boolean,
  ) => {
    if (isExpanded) {
      updateTree(itemId);
    }
  };

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
      onItemExpansionToggle={handleItemExpansionToggle}
    >
      <StudyTreeNodeComponent
        studyTreeNode={studiesTree}
        parentId=""
        itemsLoading={itemsLoading}
        onNodeClick={handleTreeItemClick}
      />
    </SimpleTreeView>
  );
}

export default StudyTree;
