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

import TreeItemEnhanced from "@/components/common/TreeItemEnhanced";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { StudyTreeNodeProps, StudyTreeNode } from "./types";

function prioritizeDefault(folderA: StudyTreeNode, folderB: StudyTreeNode): number {
  if (folderA.name === "default") {
    return -1;
  } else if (folderB.name === "default") {
    return 1;
  } else {
    return 0;
  }
}

const nameSort = R.sortBy(R.compose(R.toLower, R.prop("name")));
const defaultFirstSort = R.sortWith([prioritizeDefault]);

export default function StudyTreeNode({ node, itemsLoading, onNodeClick }: StudyTreeNodeProps) {
  const { hasChildren, children, path, name } = node;
  const isLoading = itemsLoading.includes(node.path);
  const hasUnloadedChildren = hasChildren && children.length === 0;
  const { t } = useTranslation();

  const sortedChildren = useMemo(() => {
    const sortedByName = nameSort(children);
    if (node.name === "root") {
      return defaultFirstSort(sortedByName);
    } else {
      return sortedByName;
    }
  }, [children, node.name]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItemEnhanced
      itemId={path}
      label={name}
      onClick={() => onNodeClick(node.path)}
      loading={isLoading}
    >
      {hasUnloadedChildren && (
        <TreeItemEnhanced
          itemId={`${path}//loading`}
          label={`${t("global.loading")}...`}
          sx={{ fontStyle: "italic" }}
        />
      )}
      {sortedChildren.map((child) => (
        <StudyTreeNode
          key={child.path}
          node={child}
          itemsLoading={itemsLoading}
          onNodeClick={onNodeClick}
        />
      ))}
    </TreeItemEnhanced>
  );
}
