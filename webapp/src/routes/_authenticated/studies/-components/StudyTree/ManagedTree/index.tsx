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

import { Box, Typography } from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { useSuspenseQuery } from "@tanstack/react-query";
import * as R from "ramda";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import DeleteFolderDialog from "./DeleteFolderDialog";
import EditableTreeItem from "./EditableTreeItem";
import { useDeleteFolderDialog } from "./hooks/useDeleteFolderDialog";
import { useDirectoryOperations } from "./hooks/useDirectoryOperations";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDirectoryPath } from "./utils";

function ManagedTree({ isCreatingFolder, onFolderCreated }: ManagedTreeProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const directoryId = useAppSelector((state) => getStudyFilters(state).managed.directoryId, R.T);

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const directoryTree = useMemo(() => buildDirectoryTree(directories), [directories]);

  const initialExpandedItems = useMemo(
    () => (directoryId ? getDirectoryPath(directoryTree, directoryId) : []),
    [directoryTree, directoryId],
  );

  const [expandedItems, setExpandedItems] = useState<string[]>(() => initialExpandedItems);

  const deleteDialog = useDeleteFolderDialog(directoryTree);

  const {
    startCreating,
    cancelOperation,
    createDirectory,
    isCreating,
    startUpdating,
    updateDirectory,
    isUpdating,
    deleteDirectory,
    isDeleting,
  } = useDirectoryOperations({
    onDirectoryCreated: (directory) => {
      // Expand the newly created directory
      setExpandedItems((prev) => [...prev, directory.id]);
    },
  });

  // Sync external isCreatingFolder prop with internal state
  // When parent triggers root folder creation, start with null parentId
  useEffect(() => {
    if (isCreatingFolder) {
      startCreating(null); // null = create at root level (no parent)
    }
  }, [isCreatingFolder, startCreating]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleNodeClick = (itemId: string) => {
    dispatch(
      updateStudyFilters({
        activeTree: "managed",
        managed: { directoryId: itemId },
      }),
    );
  };

  const handleSaveFolder = (parentId: string | null) => (name: string) => {
    createDirectory(name, parentId);
    onFolderCreated();
  };

  const handleCancelFolder = () => {
    cancelOperation();
    onFolderCreated();
  };

  const handleStartUpdate = (directoryId: string) => {
    startUpdating(directoryId);
  };

  const handleSaveUpdate = (directoryId: string, name: string, parentId: string | null) => {
    updateDirectory(directoryId, name, parentId);
  };

  const handleCancelUpdate = () => {
    cancelOperation();
  };

  const handleDelete = (directoryId: string) => {
    deleteDialog.openDialog(directoryId);
  };

  const handleDeleteConfirm = (cascade: boolean) => {
    if (!deleteDialog.state.directoryId) {
      return;
    }

    deleteDirectory(deleteDialog.state.directoryId, cascade, directories);
    deleteDialog.closeDialog();
  };

  const handleDeleteCancel = () => {
    deleteDialog.closeDialog();
  };

  const handleAddSubFolder = (parentId: string | null) => {
    startCreating(parentId);
    // Expand the parent node if it's not already expanded
    if (parentId && !expandedItems.includes(parentId)) {
      setExpandedItems((prev) => [...prev, parentId]);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Empty state - TODO: handle desktop mode
  if (directories.length === 0 && !isCreatingFolder) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {t("studies.tree.noDirectories", {
            defaultValue: "No directories found",
          })}
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <SimpleTreeView
        expandedItems={expandedItems}
        onExpandedItemsChange={(_event, itemIds) => setExpandedItems(itemIds)}
        defaultSelectedItems={directoryId || ""}
      >
        {/* Root level folder creation */}
        {isCreating(null) && (
          <EditableTreeItem
            itemId={`temp-root-${Date.now()}`}
            isEditing
            onSave={handleSaveFolder(null)} // null = save as root level folder
            onCancel={handleCancelFolder}
          />
        )}

        <ManagedTreeNode
          node={directoryTree}
          onNodeClick={handleNodeClick}
          selectedPath={directoryId || ""}
          onAddSubFolder={handleAddSubFolder}
          onSaveSubFolder={handleSaveFolder}
          onCancelSubFolder={handleCancelFolder}
          isCreatingSubFolder={isCreating}
          onStartUpdate={handleStartUpdate}
          onSaveUpdate={handleSaveUpdate}
          onCancelUpdate={handleCancelUpdate}
          isUpdating={isUpdating}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />
      </SimpleTreeView>

      <DeleteFolderDialog
        open={deleteDialog.state.open}
        folderName={deleteDialog.state.folderName}
        hasChildren={deleteDialog.state.hasChildren}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </>
  );
}

export default ManagedTree;
