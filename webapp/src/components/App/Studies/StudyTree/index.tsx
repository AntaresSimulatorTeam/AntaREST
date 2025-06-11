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

import { DEFAULT_WORKSPACE_NAME } from "@/components/common/utils/constants";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import * as R from "ramda";
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { updateStudyFilters } from "../../../../redux/ducks/studies";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../../redux/selectors";
import * as api from "../../../../services/api/study";
import { getParentPaths } from "../../../../utils/pathUtils";
import StudyTreeNodeComponent from "./StudyTreeNode";
import { insertIfNotExist } from "./utils";
import storage, { StorageKey } from "@/services/utils/localStorage";
import { useUpdateEffect } from "react-use";

function StudyTree() {
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  const [workspaces, setWorkspaces] = useState<string[]>([]);
  const [subFolders, setSubFolders] = useState(storage.getItem(StorageKey.StudyTreeFolders) || []);
  const [itemsLoading, setItemsLoading] = useState<string[]>([]);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const isDesktopMode = import.meta.env.MODE === "desktop";

  useEffect(() => {
    getWorkspaces().then((nextWorkspaces) => {
      const nextStudyTree = insertIfNotExist(initialStudiesTree, nextWorkspaces, subFolders);
      setStudiesTree(nextStudyTree);
      setWorkspaces(nextWorkspaces);
    });
    // subFolders isn't listed as a dependency because we don't want to trigger this code
    // otherwise we'll override studiesTree with initialStudiesTree each time the trigger a subFolders update
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialStudiesTree]);

  useUpdateEffect(() => {
    storage.setItem(StorageKey.StudyTreeFolders, subFolders);
  }, [subFolders]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

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
   * @returns void
   */
  async function updateTree(itemId: string) {
    const [root, workspace, ...subPath] = itemId.split("/");

    const isAbsolutePath = root === ""; // Path must starts with a '/'
    const isValidWorkspace = workspace && workspace !== DEFAULT_WORKSPACE_NAME;

    if (!isAbsolutePath || !isValidWorkspace) {
      return null;
    }

    setItemsLoading((prev) => [...prev, itemId]);

    // Fetch subfolders and insert them to the tree
    try {
      const newSubFolders = await api.getFolders(workspace, subPath.join("/"));

      if (newSubFolders.length > 0) {
        // use union to prioritize new subfolders
        const thisParent = ["", workspace, ...subPath].join("/");
        const otherSubfolders = subFolders.filter((f) => f.parentPath !== thisParent);
        const nextSubfolders = [...newSubFolders, ...otherSubfolders];

        setSubFolders(nextSubfolders);

        const nextStudyTree = insertIfNotExist(initialStudiesTree, workspaces, nextSubfolders);
        setStudiesTree(nextStudyTree);
      }
    } catch (err) {
      enqueueErrorSnackbar(
        t("studies.tree.error.failToFetchFolder", {
          path: itemId,
          interpolation: { escapeValue: false },
        }),
        toError(err),
      );
    }

    setItemsLoading((prev) => prev.filter((id) => id !== itemId));
  }

  /**
   *
   * Only on desktop mode it make sense to fetch the workspaces
   * as they are generated dynamically based on mounted discs
   * On web mode this case is almost neved used, so we'd rather save the API call
   *
   * @returns The list of workspaces
   */
  async function getWorkspaces() {
    if (isDesktopMode) {
      try {
        return await api.getWorkspaces();
      } catch (err) {
        enqueueErrorSnackbar(t("studies.tree.error.failToFetchWorkspace"), toError(err));
        return [];
      }
    }
    return workspaces;
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  // We need to handle both the expand event and the onClick event
  // because the onClick isn't triggered when user click on arrow.
  // Also the expanse event isn't triggered when the item doesn't have any subfolder
  // but we still want to apply the filter on the clicked folder.
  const handleItemExpansionToggle = (
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
      onItemExpansionToggle={handleItemExpansionToggle}
      sx={{ p: 2, pt: 0 }}
    >
      <StudyTreeNodeComponent
        node={studiesTree}
        itemsLoading={itemsLoading}
        onNodeClick={handleTreeItemClick}
      />
    </SimpleTreeView>
  );
}

export default StudyTree;
