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
import useUpdatedRef from "@/hooks/useUpdatedRef";
import DeleteDirectoryDialog from "./DeleteDirectoryDialog";
import EditableTreeItem from "./EditableTreeItem";
import { useDeleteDirectoryDialog } from "./hooks/useDeleteDirectoryDialog";
import { useDirectoryOperations } from "./hooks/useDirectoryOperations";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDescendantIds, getDirectoryPath } from "./utils";

function ManagedTree({ isCreatingDirectory, onDirectoryCreated }: ManagedTreeProps) {
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

  const deleteDialog = useDeleteDirectoryDialog(directoryTree);

  const operations = useDirectoryOperations({
    onDirectoryCreated: (directory) => {
      // Expand the newly created directory
      setExpandedItems((prev) => [...prev, directory.id]);
    },
  });

  // `operations.create.start` is recreated on every render (plain arrow function
  // returned from useDirectoryOperations).
  // Including it in the useEffect dependency array would cause an infinite loop.
  //
  // useUpdatedRef keeps a ref always pointing to the latest value via useLayoutEffect,
  // so the effect can safely call the latest `start` without listing it as a dependency.
  const startCreatingRef = useUpdatedRef(operations.create.start);

  useEffect(() => {
    if (isCreatingDirectory) {
      startCreatingRef.current(null); // null = create at root level (no parent)
    }
  }, [isCreatingDirectory, startCreatingRef]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleNodeClick = (itemId: string) => {
    dispatch(
      updateStudyFilters({
        activeTree: "managed",
        managed: { directoryId: itemId, directoryIds: getDescendantIds(itemId, directories) },
      }),
    );
  };

  const handleSaveDirectory = (parentId: string | null) => (name: string) => {
    operations.create.execute(name, parentId);
    onDirectoryCreated();
  };

  const handleCancelDirectory = () => {
    operations.cancel();
    onDirectoryCreated();
  };

  const handleStartUpdate = (directoryId: string) => {
    operations.update.start(directoryId);
  };

  const handleSaveUpdate = (directoryId: string, name: string, parentId: string | null) => {
    operations.update.execute(directoryId, name, parentId);
  };

  const handleCancelUpdate = () => {
    operations.cancel();
  };

  const handleDelete = (directoryId: string) => {
    deleteDialog.openDialog(directoryId);
  };

  const handleDeleteConfirm = () => {
    if (!deleteDialog.state.directoryId) {
      return;
    }

    operations.delete.execute(deleteDialog.state.directoryId, directories);
    deleteDialog.closeDialog();
  };

  const handleDeleteCancel = () => {
    deleteDialog.closeDialog();
  };

  const handleAddSubDirectory = (parentId: string | null) => {
    operations.create.start(parentId);

    // Expand the parent node if it's not already expanded
    if (parentId && !expandedItems.includes(parentId)) {
      setExpandedItems((prev) => [...prev, parentId]);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Empty state - TODO: handle desktop mode -> we can hide the managed tree ?
  if (directories.length === 0 && !isCreatingDirectory) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {t("studies.tree.noDirectories")}
        </Typography>
      </Box>
    );
  }

  return (
    <>
      {/* Root level directory creation - rendered outside SimpleTreeView to avoid
          MUI tree focus context interfering with TextField's InputBase useEffect */}
      {operations.create.isActive(null) && (
        <EditableTreeItem
          isEditing
          isPending={operations.create.isPending}
          onSave={handleSaveDirectory(null)}
          onCancel={handleCancelDirectory}
        />
      )}

      <SimpleTreeView
        expandedItems={expandedItems}
        onExpandedItemsChange={(_event, itemIds) => setExpandedItems(itemIds)}
        defaultSelectedItems={directoryId || ""}
      >
        <ManagedTreeNode
          node={directoryTree}
          onNodeClick={handleNodeClick}
          selectedPath={directoryId || ""}
          onAddSubDirectory={handleAddSubDirectory}
          onSaveSubDirectory={handleSaveDirectory}
          onCancelSubDirectory={handleCancelDirectory}
          isCreatingSubDirectory={operations.create.isActive}
          isCreatePending={operations.create.isPending}
          onStartUpdate={handleStartUpdate}
          onSaveUpdate={handleSaveUpdate}
          onCancelUpdate={handleCancelUpdate}
          isUpdating={operations.update.isActive}
          isUpdatePending={operations.update.isPending}
          onDelete={handleDelete}
          isDeleting={operations.delete.isActive}
          isDeletePending={operations.delete.isPending}
        />
      </SimpleTreeView>

      <DeleteDirectoryDialog
        open={deleteDialog.state.open}
        directoryName={deleteDialog.state.directoryName}
        hasChildren={deleteDialog.state.hasChildren}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </>
  );
}

export default ManagedTree;
