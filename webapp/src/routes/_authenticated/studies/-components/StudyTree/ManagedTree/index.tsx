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

import { directoryQueries } from "@/queries/directories/queries";
import { directoryMutations } from "@/queries/directories/mutations";
import { directoryKeys } from "@/queries/directories/keys";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import { Box, Typography } from "@mui/material";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { Directory } from "@/services/api/directories/types";
import EditableTreeItem from "./EditableTreeItem";
import ManagedTreeNode from "./ManagedTreeNode";
import type { ManagedTreeProps } from "./types";
import { buildDirectoryTree, getDirectoryPath } from "./utils";

function ManagedTree({
  studies,
  onNodeClick,
  isCreatingFolder,
  onFolderCreated,
}: ManagedTreeProps) {
  const { t } = useTranslation();
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const queryClient = useQueryClient();

  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const directoryTree = useMemo(() => buildDirectoryTree(directories), [directories]);

  const expandedItems = useMemo(
    () => (folder ? getDirectoryPath(directoryTree, folder) : []),
    [directoryTree, folder],
  );

  const createMutation = useMutation({
    ...directoryMutations.create(),
    onMutate: async (newDirectory) => {
      // Hide the editable item and notify parent
      onFolderCreated();

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: directoryKeys.all });

      // Snapshot previous value
      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      // Optimistically update with temporary directory
      if (previousDirectories) {
        const tempDirectory: Directory = {
          id: `temp-${Date.now()}`,
          name: newDirectory.name,
          parentId: newDirectory.parentId,
        };

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), [
          ...previousDirectories,
          tempDirectory,
        ]);
      }

      return { previousDirectories };
    },
    onError: (_err, _newDirectory, context) => {
      // Rollback on error
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }
    },
    onSuccess: () => {
      // Refetch to get the real ID from server
      queryClient.invalidateQueries({ queryKey: directoryKeys.all });
    },
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = (name: string) => {
    createMutation.mutate({
      name,
      parentId: null, // null for root level directories
    });
  };

  const handleCancel = () => {
    onFolderCreated();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Empty state
  // TODO: handle desktop mode - it may not require an empty state
  // TODO: add "studies.tree.noDirectories" key
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
      {isCreatingFolder && (
        <EditableTreeItem
          itemId={`temp-${Date.now()}`}
          isEditing
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
      <ManagedTreeNode node={directoryTree} onNodeClick={onNodeClick} selectedPath={folder} />
    </SimpleTreeView>
  );
}

export default ManagedTree;
