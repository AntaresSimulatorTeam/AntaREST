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
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Box, IconButton, Tooltip } from "@mui/material";
import * as R from "ramda";
import { useMemo } from "react";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import EditableTreeItem from "./EditableTreeItem";
import {
  actionButtonStyles,
  addSubFolderIconStyles,
  deleteIconStyles,
  nodeActionsContainerStyles,
  nodeLabelContainerStyles,
  renameIconStyles,
  treeItemStyles,
  treeNodeIcons,
} from "./styles";
import type { ManagedTreeNodeProps } from "./types";

function ManagedTreeNode({
  node,
  onNodeClick,
  selectedPath,
  onAddSubFolder,
  onSaveSubFolder,
  onCancelSubFolder,
  isCreatingSubFolder,
  onStartUpdate,
  onSaveUpdate,
  onCancelUpdate,
  isUpdating,
  onDelete,
  isDeleting,
}: ManagedTreeNodeProps) {
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

  const handleAddSubFolder = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAddSubFolder(id); // id becomes the parentId for the new subfolder
  };

  const handleStartUpdate = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStartUpdate(id);
  };

  const handleSaveUpdate = (newName: string) => {
    onSaveUpdate(id, newName, node.parentId);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(id);
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
            onStartUpdate={onStartUpdate}
            onSaveUpdate={onSaveUpdate}
            onCancelUpdate={onCancelUpdate}
            isUpdating={isUpdating}
            onDelete={onDelete}
            isDeleting={isDeleting}
          />
        ))}
      </>
    );
  }

  // If this directory is in update mode, render editable item
  if (isUpdating(id)) {
    return (
      <EditableTreeItem
        itemId={path}
        initialValue={name}
        isEditing
        onSave={handleSaveUpdate}
        onCancel={onCancelUpdate}
      />
    );
  }

  return (
    <TreeItemEnhanced
      itemId={path}
      label={
        <Box sx={nodeLabelContainerStyles}>
          <Tooltip title={name}>
            <Box
              component="span"
              sx={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
            >
              {name}
            </Box>
          </Tooltip>
          <Box sx={nodeActionsContainerStyles}>
            <IconButton size="small" onClick={handleAddSubFolder} sx={actionButtonStyles}>
              <CreateNewFolderIcon sx={addSubFolderIconStyles} />
            </IconButton>
            <IconButton size="small" onClick={handleStartUpdate} sx={actionButtonStyles}>
              <EditIcon sx={renameIconStyles} />
            </IconButton>
            <IconButton size="small" onClick={handleDelete} sx={actionButtonStyles}>
              <DeleteIcon sx={deleteIconStyles} />
            </IconButton>
          </Box>
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
          onStartUpdate={onStartUpdate}
          onSaveUpdate={onSaveUpdate}
          onCancelUpdate={onCancelUpdate}
          isUpdating={isUpdating}
          onDelete={onDelete}
          isDeleting={isDeleting}
        />
      ))}
    </TreeItemEnhanced>
  );
}

export default ManagedTreeNode;
