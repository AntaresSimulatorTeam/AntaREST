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

import RadarIcon from "@mui/icons-material/Radar";
import { Tooltip } from "@mui/material";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { DEFAULT_WORKSPACE_NAME, ROOT_NODE_NAME } from "@/components/utils/constants";
import { treeItemStyles, treeNodeIcons, workspaceItemStyles } from "./styles";
import type { ExternalTreeNodeMetadata, ExternalTreeNodeProps } from "./types";

// Prioritizes the default workspace in sorting
const prioritizeDefault = (
  folderA: ExternalTreeNodeMetadata,
  folderB: ExternalTreeNodeMetadata,
): number => {
  if (folderA.name === DEFAULT_WORKSPACE_NAME) {
    return -1;
  }
  if (folderB.name === DEFAULT_WORKSPACE_NAME) {
    return 1;
  }
  return 0;
};

const sortByName = R.sortBy<ExternalTreeNodeMetadata>(R.compose(R.toLower, R.prop("name")));
const sortDefaultFirst = R.sortWith<ExternalTreeNodeMetadata>([prioritizeDefault]);
const filterScannedStudies = R.reject<ExternalTreeNodeMetadata>(
  (node) => node.isScannedStudy === true,
);

const isWorkspacePath = (path: string): boolean =>
  path.startsWith("/") && !path.slice(1).includes("/");

function ExternalTreeNode({
  node,
  itemsLoading,
  onNodeClick,
  exploredFolders,
}: ExternalTreeNodeProps) {
  const { hasChildren, children, path, name, isStudyFolder, alias } = node;
  const { t } = useTranslation();

  const isLoading = itemsLoading.includes(path);
  const hasUnloadedChildren =
    hasChildren && children.length === 0 && !exploredFolders.includes(path);
  const isWorkspace = isWorkspacePath(path);

  const sortedChildren = useMemo(() => {
    const nodesToDisplay = filterScannedStudies(children);
    const sortedByName = sortByName(nodesToDisplay);
    return name === ROOT_NODE_NAME ? sortDefaultFirst(sortedByName) : sortedByName;
  }, [children, name]);

  const label = alias ? `${alias} (${name})` : name;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Special handling for unscanned study folders with radar icon
  if (isStudyFolder) {
    return (
      <TreeItemEnhanced
        itemId={path}
        label={label}
        disabled
        slots={{
          collapseIcon: () => (
            <Tooltip title={t("studies.tree.unscannedStudyFolder")}>
              <RadarIcon color="warning" />
            </Tooltip>
          ),
        }}
        sx={{
          ...treeItemStyles,
          ".Mui-disabled": {
            opacity: 1,
            cursor: "default",
          },
        }}
      />
    );
  }

  return (
    <TreeItemEnhanced
      itemId={path}
      label={label}
      onClick={() => onNodeClick(path)}
      loading={isLoading}
      slots={{
        collapseIcon: isWorkspace ? treeNodeIcons.workspace : treeNodeIcons.folderOpen,
        expandIcon: isWorkspace ? treeNodeIcons.workspace : treeNodeIcons.folder,
      }}
      disableTooltip
      sx={isWorkspace ? workspaceItemStyles : treeItemStyles}
    >
      {/* Loading placeholder to show expand arrow for folders with unloaded children */}
      {hasUnloadedChildren && (
        <TreeItemEnhanced
          itemId={`${path}//loading`}
          label={`${t("global.loading")}...`}
          disableTooltip
          sx={{ fontStyle: "italic" }}
        />
      )}
      {sortedChildren.map((child) => (
        <ExternalTreeNode
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

export default ExternalTreeNode;
