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

import { useState } from "react";
import { useCreateDirectory } from "./useCreateDirectory";
import { useDeleteDirectory } from "./useDeleteDirectory";
import { useUpdateDirectory } from "./useUpdateDirectory";

export interface DirectoryOperation {
  type: "create" | "update" | "delete";
  parentId?: string | null; // For create: null = root level, string = subdirectory of parent
  directoryId?: string; // For update/delete: ID of directory being modified
}

export function useDirectoryOperations() {
  const [currentOperation, setCurrentOperation] = useState<DirectoryOperation | null>(null);

  const createMutation = useCreateDirectory({
    onSuccess: () => {
      setCurrentOperation(null);
    },
  });

  const updateMutation = useUpdateDirectory({
    onSuccess: () => {
      setCurrentOperation(null);
    },
  });

  const deleteMutation = useDeleteDirectory({
    onSuccess: () => {
      setCurrentOperation(null);
    },
  });

  ////////////////////////////////////////////////////////////////
  // Create operations
  ////////////////////////////////////////////////////////////////

  const startCreating = (parentId: string | null) => {
    setCurrentOperation({ type: "create", parentId });
  };

  const createDirectory = (name: string, parentId: string | null) => {
    createMutation.mutate({ name, parentId });
  };

  const isCreating = (parentId: string | null) => {
    return currentOperation?.type === "create" && currentOperation.parentId === parentId;
  };

  ////////////////////////////////////////////////////////////////
  // Update operations
  ////////////////////////////////////////////////////////////////

  const startUpdating = (directoryId: string) => {
    setCurrentOperation({ type: "update", directoryId });
  };

  const updateDirectory = (directoryId: string, name: string, parentId: string | null) => {
    updateMutation.mutate({ id: directoryId, data: { name, parentId } });
  };

  const isUpdating = (directoryId: string) => {
    return currentOperation?.type === "update" && currentOperation.directoryId === directoryId;
  };

  ////////////////////////////////////////////////////////////////
  // Delete operations
  ////////////////////////////////////////////////////////////////

  const startDeleting = (directoryId: string) => {
    setCurrentOperation({ type: "delete", directoryId });
  };

  const deleteDirectory = (directoryId: string) => {
    deleteMutation.mutate(directoryId);
  };

  const isDeleting = (directoryId: string) => {
    return currentOperation?.type === "delete" && currentOperation.directoryId === directoryId;
  };

  ////////////////////////////////////////////////////////////////
  // Shared operations
  ////////////////////////////////////////////////////////////////

  const cancelOperation = () => {
    setCurrentOperation(null);
  };

  ////////////////////////////////////////////////////////////////
  // Return
  ////////////////////////////////////////////////////////////////

  return {
    // State
    currentOperation,

    // Create operations
    startCreating,
    cancelOperation,
    createDirectory,
    isCreating,
    isCreatingLoading: createMutation.isPending,

    // Update operations
    startUpdating,
    updateDirectory,
    isUpdating,
    isUpdatingLoading: updateMutation.isPending,

    // Delete operations
    startDeleting,
    deleteDirectory,
    isDeleting,
    isDeletingLoading: deleteMutation.isPending,
  };
}
