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

import { StudyTreeNode } from "./utils";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../redux/ducks/studies";
import TreeItemEnhanced from "../../common/TreeItemEnhanced";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../utils/pathUtils";
import * as R from "ramda";

function StudyTree() {
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const studiesTree = useAppSelector(getStudiesTree);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
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
          onClick={() => handleTreeItemClick(id)}
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
        overflowY: "auto",
        overflowX: "hidden",
        width: 1,
        py: 1,
      }}
    >
      {buildTree([studiesTree])}
    </SimpleTreeView>
  );
}

export default StudyTree;
