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
import { Box, IconButton } from "@mui/material";
import * as R from "ramda";
import { useMemo } from "react";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import EditableTreeItem from "./EditableTreeItem";
import {
  actionButtonStyles,
  addSubDirectoryIconStyles,
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
  onAddSubDirectory,
  onSaveSubDirectory,
  onCancelSubDirectory,
  isCreatingSubDirectory,
  isCreatePending,
  onStartUpdate,
  onSaveUpdate,
  onCancelUpdate,
  isUpdating,
  isUpdatePending,
  onDelete,
  isDeleting,
  isDeletePending,
}: ManagedTreeNodeProps) {
  const { children, path, name, id } = node;
  const isRootNode = name === ROOT_NODE_NAME;
  const sortedChildren = useMemo(
    () => R.sortBy(R.compose(R.toLower, R.prop("name")), children),
    [children],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAddSubDirectory = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAddSubDirectory(id); // id becomes the parentId for the new subdirectory
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
            onAddSubDirectory={onAddSubDirectory}
            onSaveSubDirectory={onSaveSubDirectory}
            onCancelSubDirectory={onCancelSubDirectory}
            isCreatingSubDirectory={isCreatingSubDirectory}
            isCreatePending={isCreatePending}
            onStartUpdate={onStartUpdate}
            onSaveUpdate={onSaveUpdate}
            onCancelUpdate={onCancelUpdate}
            isUpdating={isUpdating}
            isUpdatePending={isUpdatePending}
            onDelete={onDelete}
            isDeleting={isDeleting}
            isDeletePending={isDeletePending}
          />
        ))}
      </>
    );
  }

  // If this directory is in update mode, render editable item
  if (isUpdating(id)) {
    return (
      <EditableTreeItem
        initialValue={name}
        isEditing
        isPending={isUpdatePending}
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
          <Box
            component="span"
            sx={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
          >
            {name}
          </Box>
          <Box sx={nodeActionsContainerStyles}>
            <IconButton size="small" onClick={handleAddSubDirectory} sx={actionButtonStyles}>
              <CreateNewFolderIcon sx={addSubDirectoryIconStyles} />
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
        collapseIcon: treeNodeIcons.folderOpen,
        expandIcon: treeNodeIcons.folder,
        endIcon: treeNodeIcons.folder,
      }}
      sx={treeItemStyles}
    >
      {/* Show editable item when creating a subdirectory under this directory */}
      {isCreatingSubDirectory(id) && (
        <EditableTreeItem
          isEditing
          isPending={isCreatePending}
          onSave={onSaveSubDirectory(id)} // id is the parentId for the new subdirectory
          onCancel={onCancelSubDirectory}
        />
      )}

      {/* Recursively render child directories */}
      {sortedChildren.map((child) => (
        <ManagedTreeNode
          key={child.id}
          node={child}
          onNodeClick={onNodeClick}
          selectedPath={selectedPath}
          onAddSubDirectory={onAddSubDirectory}
          onSaveSubDirectory={onSaveSubDirectory}
          onCancelSubDirectory={onCancelSubDirectory}
          isCreatingSubDirectory={isCreatingSubDirectory}
          isCreatePending={isCreatePending}
          onStartUpdate={onStartUpdate}
          onSaveUpdate={onSaveUpdate}
          onCancelUpdate={onCancelUpdate}
          isUpdating={isUpdating}
          isUpdatePending={isUpdatePending}
          onDelete={onDelete}
          isDeleting={isDeleting}
          isDeletePending={isDeletePending}
        />
      ))}
    </TreeItemEnhanced>
  );
}

export default ManagedTreeNode;
