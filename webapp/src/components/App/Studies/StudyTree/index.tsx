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
import { AxiosError } from "axios";

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
    const initializeFolders = async () => {
      try {
        const treeWithWorkspaces =
          await fetchAndInsertWorkspaces(initialStudiesTree);
        const childrenPaths = treeWithWorkspaces.children.map(
          (child) => `root${child.path}`,
        );
        const [updatedTree, failedPaths] = await fetchAndInsertSubfolders(
          childrenPaths,
          treeWithWorkspaces,
        );
        setStudiesTree(updatedTree);
        failedPaths.forEach((path) => {
          enqueueErrorSnackbar(
            t("studies.tree.error.failToFetchFolder", {
              path,
              interpolation: { escapeValue: false },
            }),
            t("studies.tree.error.detailsInConsole"),
          );
        });
      } catch (error) {
        setStudiesTree(initialStudiesTree);
        enqueueErrorSnackbar(
          t("studies.tree.error.failToFetchWorkspace"),
          error as AxiosError,
        );
      }
    };

    initializeFolders();
  }, [initialStudiesTree]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = async (
    itemId: string,
    studyTreeNode: StudyTreeNode,
  ) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    if (itemId === "root") {
      try {
        const nextTree = await fetchAndInsertWorkspaces(studiesTree);
        setStudiesTree(nextTree);
      } catch (error) {
        enqueueErrorSnackbar(
          "studies.tree.error.failToFetchWorkspace",
          error as AxiosError,
        );
      }
    }
    const chidrenPaths = studyTreeNode.children.map(
      (child) => `root${child.path}`,
    );
    // children paths and current element path
    const [nextTree, failedPath] = await fetchAndInsertSubfolders(
      chidrenPaths,
      studiesTree,
    );
    setStudiesTree(nextTree);
    for (const path of failedPath) {
      enqueueErrorSnackbar(
        t("studies.tree.error.failToFetchFolder", {
          path,
          interpolation: { escapeValue: false },
        }),
        t("studies.tree.error.detailsInConsole"),
      );
    }
  };
  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const buildTree = (children: StudyTreeNode[], parentId?: string) => {
    return children.map((elm) => {
      const id = parentId ? `${parentId}/${elm.name}` : elm.name;

      return (
        <TreeItemEnhanced
          key={id}
          itemId={id}
          label={elm.name}
          onClick={() => handleTreeItemClick(id, elm)}
        >
          {buildTree(elm.children, id)}
        </TreeItemEnhanced>
      );
    });
  };

  return (
    <SimpleTreeView
      defaultExpandedItems={[...getParentPaths(folder), folder]}
      defaultSelectedItems={folder}
      sx={{ flexGrow: 1, height: 0, width: 1, py: 1 }}
    >
      {buildTree([studiesTree])}
    </SimpleTreeView>
  );
}

export default StudyTree;
