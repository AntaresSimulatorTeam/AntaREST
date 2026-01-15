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

export interface DirectoryOperation {
  type: "create" | "update" | "delete";
  parentId: string | null; // null = root level directory, string = subdirectory of parent
}

export function useDirectoryOperations() {
  const [currentOperation, setCurrentOperation] = useState<DirectoryOperation | null>(null);

  const createMutation = useCreateDirectory({
    onSuccess: () => {
      setCurrentOperation(null);
    },
  });

  const startCreating = (parentId: string | null) => {
    setCurrentOperation({ type: "create", parentId });
  };

  const cancelOperation = () => {
    setCurrentOperation(null);
  };

  const createDirectory = (name: string, parentId: string | null) => {
    createMutation.mutate({ name, parentId });
  };

  // null to check root level, directory ID to check subfolder
  const isCreating = (parentId: string | null) => {
    return currentOperation?.type === "create" && currentOperation.parentId === parentId;
  };

  // Future: Add update and delete handlers here
  // const updateDirectory = (id: string, name: string) => { ... }
  // const deleteDirectory = (id: string) => { ... }
  // const isUpdating = (id: string) => { ... }
  // const isDeleting = (id: string) => { ... }

  return {
    // State
    currentOperation,

    // Create operations
    startCreating,
    cancelOperation,
    createDirectory,
    isCreating,
    isCreatingLoading: createMutation.isPending,

    // Future: Export update/delete operations
    // updateDirectory,
    // deleteDirectory,
    // isUpdating,
    // isDeleting,
  };
}
