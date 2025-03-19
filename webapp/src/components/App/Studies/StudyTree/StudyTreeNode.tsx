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

import { useMemo } from "react";
import * as R from "ramda";
import type { StudyTreeNodeProps } from "./types";
import TreeItemEnhanced from "@/components/common/TreeItemEnhanced";
import { t } from "i18next";

export default function StudyTreeNode({
  studyTreeNode,
  parentId,
  itemsLoading,
  onNodeClick,
}: StudyTreeNodeProps) {
  const id = parentId ? `${parentId}/${studyTreeNode.name}` : studyTreeNode.name;
  const isLoadingFolder = itemsLoading.includes(id);
  const hasUnloadedChildern = studyTreeNode.hasChildren && studyTreeNode.children.length === 0;
  const sortedChildren = useMemo(
    () => R.sortBy(R.compose(R.toLower, R.prop("name")), studyTreeNode.children),
    [studyTreeNode.children],
  );

  // Either the user clicked on the folder and we need to show the folder is loading
  // Or the explorer api says that this folder has children so we need to load at least one element
  // so the arrow to explanse the element is displayed which indicate to the user that this is a folder
  if (isLoadingFolder || hasUnloadedChildern) {
    return (
      <TreeItemEnhanced itemId={id} label={studyTreeNode.name}>
        <TreeItemEnhanced itemId={id + "loading"} label={t("studies.tree.fetchFolderLoading")} />
      </TreeItemEnhanced>
    );
  }

  return (
    <TreeItemEnhanced itemId={id} label={studyTreeNode.name} onClick={() => onNodeClick(id)}>
      {sortedChildren.map((child) => (
        <StudyTreeNode
          key={`${id}/${child.name}`}
          studyTreeNode={child}
          parentId={id}
          itemsLoading={itemsLoading}
          onNodeClick={onNodeClick}
        />
      ))}
    </TreeItemEnhanced>
  );
}
