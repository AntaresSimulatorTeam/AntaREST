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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { useLatest } from "react-use";
import usePrevious from "react-use/lib/usePrevious";
import * as R from "ramda";
import { directoryQueries } from "@/queries/directories/queries";
import { finishStudyFolderReveal, updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters, getStudyFolderRevealRequest } from "@/redux/selectors";
import { getDescendantIds } from "@/utils/directoryUtils";
import { Box, Typography } from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useRevealTreeItem from "../hooks/useRevealTreeItem";
import DeleteDirectoryDialog from "./DeleteDirectoryDialog";
import EditableTreeItem from "./EditableTreeItem";
import { useDeleteDirectoryDialog } from "./hooks/useDeleteDirectoryDialog";
import { useDirectoryOperations } from "./hooks/useDirectoryOperations";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDirectoryPath } from "./utils";

function ManagedTree({ isCreatingDirectory, onDirectoryCreated }: ManagedTreeProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { directoryId, directoryIds } = useAppSelector((state) => getStudyFilters(state).managed);
  const isActive = useAppSelector((state) => getStudyFilters(state).activeTree === "managed");
  const revealRequest = useAppSelector((state) => {
    const request = getStudyFolderRevealRequest(state);

    return request?.tree === "managed" ? request : null;
  });

  const { data: directories, fetchStatus, error } = useSuspenseQuery(directoryQueries.list());

  const directoryTree = useMemo(() => buildDirectoryTree(directories), [directories]);

  const prevDirectoryId = usePrevious(directoryId);
  const [expandedItems, setExpandedItems] = useState<string[]>(() =>
    directoryId ? getDirectoryPath(directoryTree, directoryId) : [],
  );

  // Links outside the tree must also expand the selected folder's ancestors.
  if (prevDirectoryId !== directoryId) {
    const required = directoryId ? getDirectoryPath(directoryTree, directoryId) : [];
    const missing = R.difference(required, expandedItems);

    if (missing.length > 0) {
      setExpandedItems([...expandedItems, ...missing]);
    }
  }

  const requiredPath = useMemo(
    () => (directoryId ? getDirectoryPath(directoryTree, directoryId) : []),
    [directoryId, directoryTree],
  );
  const directoryExists = directoryId === null || requiredPath.length > 0;

  useEffect(() => {
    // A cached miss is not final while the directory query is fetching or paused.
    if (
      !revealRequest ||
      revealRequest.directoryId === null ||
      directoryExists ||
      fetchStatus !== "idle"
    ) {
      return;
    }

    enqueueErrorSnackbar(
      t("studies.tree.error.folderUnavailable"),
      error ?? revealRequest.directoryId,
    );
    dispatch(finishStudyFolderReveal(revealRequest.requestId));
  }, [revealRequest, directoryExists, fetchStatus, error, enqueueErrorSnackbar, t, dispatch]);

  useEffect(() => {
    if (!isActive || !directoryExists) {
      return;
    }

    const nextDirectoryIds = directoryId ? getDescendantIds(directoryId, directories) : null;

    if (!R.equals(directoryIds, nextDirectoryIds)) {
      // Updating only the scope preserves any reveal still waiting for layout.
      dispatch(updateStudyFilters({ managed: { directoryIds: nextDirectoryIds } }));
    }
  }, [directories, directoryId, directoryIds, directoryExists, isActive, dispatch]);

  useEffect(() => {
    if (revealRequest) {
      setExpandedItems((previous) => R.union(previous, requiredPath));
    }
  }, [revealRequest, requiredPath]);

  const { treeRef, apiRef } = useRevealTreeItem({
    requestId: revealRequest?.requestId,
    itemId: directoryId,
    ready: directoryExists && requiredPath.every((id) => expandedItems.includes(id)),
  });

  const deleteDialog = useDeleteDirectoryDialog(directoryTree);

  const operations = useDirectoryOperations({
    onDirectoryCreated: (directory) => {
      setExpandedItems((prev) => [...prev, directory.id]);
    },
  });

  // `create.start` changes identity each render and updates state when called.
  // Depending on it directly would loop while creation is active.
  // `useLatest` supplies the current handler through a stable ref.
  const startCreatingRef = useLatest(operations.create.start);

  useEffect(() => {
    if (isCreatingDirectory) {
      startCreatingRef.current(null); // null = create at root level (no parent)
    }
  }, [isCreatingDirectory, startCreatingRef]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleItemClick = (_event: React.MouseEvent, itemId: string) => {
    dispatch(
      updateStudyFilters({
        activeTree: "managed",
        managed: {
          directoryId: itemId,
          directoryIds: getDescendantIds(itemId, directories),
        },
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

    if (parentId && !expandedItems.includes(parentId)) {
      setExpandedItems((prev) => [...prev, parentId]);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {directories.length === 0 && !isCreatingDirectory && (
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t("studies.tree.noDirectories")}
          </Typography>
        </Box>
      )}
      {/* Keep root creation outside the tree so its focus handling does not intercept the input. */}
      {operations.create.isActive(null) && (
        <EditableTreeItem
          isEditing
          isPending={operations.create.isPending}
          onSave={handleSaveDirectory(null)}
          onCancel={handleCancelDirectory}
        />
      )}

      <SimpleTreeView
        ref={treeRef}
        apiRef={apiRef}
        expandedItems={expandedItems}
        onExpandedItemsChange={(_event, itemIds) => setExpandedItems(itemIds)}
        selectedItems={isActive ? directoryId : null}
        onItemClick={handleItemClick}
      >
        <ManagedTreeNode
          node={directoryTree}
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
