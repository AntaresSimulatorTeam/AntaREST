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

import { memo, useMemo } from "react";
import * as R from "ramda";
import type { StudyTreeNodeProps } from "./types";
import TreeItemEnhanced from "@/components/common/TreeItemEnhanced";
import { t } from "i18next";

export default memo(function StudyTreeNode({
  studyTreeNode,
  parentId,
  itemsLoading,
}: StudyTreeNodeProps) {
  const id = parentId ? `${parentId}/${studyTreeNode.name}` : studyTreeNode.name;
  const isLoadingFolder = itemsLoading.includes(id);

  const sortedChildren = useMemo(
    () => R.sortBy(R.prop("name"), studyTreeNode.children),
    [studyTreeNode.children],
  );

  if (isLoadingFolder) {
    return (
      <TreeItemEnhanced itemId={id} label={studyTreeNode.name}>
        <TreeItemEnhanced itemId={id + "loading"} label={t("studies.tree.fetchFolderLoading")} />
      </TreeItemEnhanced>
    );
  }

  return (
    <TreeItemEnhanced itemId={id} label={studyTreeNode.name}>
      {sortedChildren.map((child) => (
        <StudyTreeNode
          key={`${id}/${child.name}`}
          studyTreeNode={child}
          parentId={id}
          itemsLoading={itemsLoading}
        />
      ))}
    </TreeItemEnhanced>
  );
});
