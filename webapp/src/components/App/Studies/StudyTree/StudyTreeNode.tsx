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
import { DEFAULT_WORKSPACE_NAME, ROOT_NODE_NAME } from "@/components/common/utils/constants";
import RadarIcon from "@mui/icons-material/Radar";
import { Tooltip } from "@mui/material";

function prioritizeDefault(folderA: StudyTreeNode, folderB: StudyTreeNode): number {
  if (folderA.name === DEFAULT_WORKSPACE_NAME) {
    return -1;
  } else if (folderB.name === DEFAULT_WORKSPACE_NAME) {
    return 1;
  } else {
    return 0;
  }
}

const nameSort = R.sortBy(R.compose(R.toLower, R.prop("name")));
const defaultFirstSort = R.sortWith([prioritizeDefault]);

export default function StudyTreeNode({
  node,
  itemsLoading,
  onNodeClick,
  exploredFolders,
}: StudyTreeNodeProps) {
  const { hasChildren, children, path, name, isStudyFolder, alias } = node;
  const isLoading = itemsLoading.includes(node.path);
  const hasUnloadedChildren =
    hasChildren && children.length === 0 && !exploredFolders.includes(node.path);
  const { t } = useTranslation();

  const sortedChildren = useMemo(() => {
    const nonStudyChildren = children.filter((s) => !s.isScannedStudy);
    const sortedByName = nameSort(nonStudyChildren);
    if (node.name === ROOT_NODE_NAME) {
      return defaultFirstSort(sortedByName);
    }
    return sortedByName;
  }, [children, node.name]);

  const label = alias ? `${alias} (${name})` : name;
  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////
  return (
    <TreeItemEnhanced
      itemId={path}
      label={label}
      slots={
        isStudyFolder
          ? {
              icon: () => (
                <Tooltip title={t("studies.tree.unscannedStudyFolder")}>
                  <RadarIcon color="warning" />
                </Tooltip>
              ),
            }
          : undefined
      }
      onClick={isStudyFolder ? undefined : () => onNodeClick(node.path)}
      disabled={isStudyFolder}
      sx={{
        ".Mui-disabled": {
          opacity: 1,
          cursor: "default",
        },
      }}
      loading={isLoading}
    >
      {/* the loading tree item bellow may seem useless but it's mandatory to display  
          the little arrow on the left on folders without scanned studies*/}
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
          exploredFolders={exploredFolders}
        />
      ))}
    </TreeItemEnhanced>
  );
}
