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
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { directoryQueries } from "@/queries/directories/queries";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import EditableTreeItem from "./EditableTreeItem";
import { useDirectoryOperations } from "./hooks/useDirectoryOperations";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDirectoryPath } from "./utils";

function ManagedTree({ onNodeClick, isCreatingFolder, onFolderCreated }: ManagedTreeProps) {
  const { t } = useTranslation();
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const directoryTree = useMemo(() => buildDirectoryTree(directories), [directories]);

  const expandedItems = useMemo(
    () => (folder ? getDirectoryPath(directoryTree, folder) : []),
    [directoryTree, folder],
  );

  const { startCreating, cancelOperation, createDirectory, isCreating } = useDirectoryOperations();

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

  /**
   * Curried handler for saving folders at any level
   *
   * @param parentId - null for root level folder, directory ID for subfolder
   * @returns Function that accepts the folder name
   */
  const handleSaveFolder = (parentId: string | null) => (name: string) => {
    createDirectory(name, parentId);
    onFolderCreated();
  };

  const handleCancelFolder = () => {
    cancelOperation();
    onFolderCreated();
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
    <SimpleTreeView defaultExpandedItems={expandedItems} defaultSelectedItems={folder}>
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
        onNodeClick={onNodeClick}
        selectedPath={folder}
        onAddSubFolder={startCreating} // Pass parentId to create subfolder
        onSaveSubFolder={handleSaveFolder} // Curried: (parentId) => (name) => save
        onCancelSubFolder={handleCancelFolder}
        isCreatingSubFolder={isCreating} // Check if creating under specific parent
      />
    </SimpleTreeView>
  );
}

export default ManagedTree;
