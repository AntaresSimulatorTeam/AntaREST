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

import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import { Box, IconButton, Tooltip } from "@mui/material";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import EditableTreeItem from "./EditableTreeItem";
import { treeItemStyles, treeNodeIcons } from "./styles";
import type { ManagedTreeNodeProps } from "./types";

function ManagedTreeNode({
  node,
  onNodeClick,
  selectedPath,
  onAddSubFolder,
  onSaveSubFolder,
  onCancelSubFolder,
  isCreatingSubFolder,
}: ManagedTreeNodeProps) {
  const { t } = useTranslation();
  const { children, path, name, id } = node;
  const isRootNode = name === ROOT_NODE_NAME;
  const hasChildren = children.length > 0;

  const sortedChildren = useMemo(
    () => R.sortBy(R.compose(R.toLower, R.prop("name")), children),
    [children],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  /**
   * Trigger subfolder creation for this directory
   * Passes the current node's ID as the parentId
   *
   * @param e
   */
  const handleAddSubFolder = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAddSubFolder(id); // id becomes the parentId for the new subfolder
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Root node is just a container - it doesn't render itself, only its children
  // Children of root node are top-level directories (parentId === null in the API)
  if (isRootNode) {
    return (
      <>
        {sortedChildren.map((child) => (
          <ManagedTreeNode
            key={child.id}
            node={child}
            onNodeClick={onNodeClick}
            selectedPath={selectedPath}
            onAddSubFolder={onAddSubFolder}
            onSaveSubFolder={onSaveSubFolder}
            onCancelSubFolder={onCancelSubFolder}
            isCreatingSubFolder={isCreatingSubFolder}
          />
        ))}
      </>
    );
  }

  return (
    <TreeItemEnhanced
      itemId={path}
      label={
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
            pr: 0.5,
          }}
        >
          <Box component="span">{name}</Box>
          <Tooltip
            title={t("studies.tree.addSubFolder", { defaultValue: "Add subfolder" })}
            placement="right"
            arrow
          >
            <IconButton
              size="small"
              onClick={handleAddSubFolder}
              sx={{
                p: 0.25,
                opacity: 0,
                ".MuiTreeItem-content:hover &": {
                  opacity: 1,
                },
                "&:hover": {
                  backgroundColor: (theme) => `${theme.palette.info.main}20`,
                },
              }}
              aria-label={t("studies.tree.addSubFolder", { defaultValue: "Add subfolder" })}
            >
              <CreateNewFolderIcon sx={{ fontSize: 16, color: "info.main" }} />
            </IconButton>
          </Tooltip>
        </Box>
      }
      onClick={() => onNodeClick(path)}
      slots={{
        collapseIcon: hasChildren ? treeNodeIcons.folderOpen : undefined,
        expandIcon: hasChildren ? treeNodeIcons.folder : undefined,
      }}
      sx={treeItemStyles}
    >
      {/* Show editable item when creating a subfolder under this directory */}
      {isCreatingSubFolder(id) && (
        <EditableTreeItem
          itemId={`temp-${id}-${Date.now()}`}
          isEditing
          onSave={onSaveSubFolder(id)} // id is the parentId for the new subfolder
          onCancel={onCancelSubFolder}
        />
      )}

      {/* Recursively render child directories */}
      {sortedChildren.map((child) => (
        <ManagedTreeNode
          key={child.id}
          node={child}
          onNodeClick={onNodeClick}
          selectedPath={selectedPath}
          onAddSubFolder={onAddSubFolder}
          onSaveSubFolder={onSaveSubFolder}
          onCancelSubFolder={onCancelSubFolder}
          isCreatingSubFolder={isCreatingSubFolder}
        />
      ))}
    </TreeItemEnhanced>
  );
}

export default ManagedTreeNode;
