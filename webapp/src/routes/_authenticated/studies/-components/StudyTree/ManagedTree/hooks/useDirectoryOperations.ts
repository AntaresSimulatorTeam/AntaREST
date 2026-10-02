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
import type { Directory } from "@/services/api/directories/types";
import { useCreateDirectory } from "./useCreateDirectory";
import { useDeleteDirectory } from "./useDeleteDirectory";
import { useUpdateDirectory } from "./useUpdateDirectory";

/**
 * Represents the current UI operation being performed on a directory.
 * This is UI state that tracks which directory is in "edit mode" or "create mode",
 * separate from the API mutation state.
 */
export interface DirectoryOperation {
  type: "create" | "update" | "delete";
  parentId?: string | null; // For create: null = root level, string = subdirectory of parent
  directoryId?: string; // For update/delete: ID of directory being modified
}

export interface UseDirectoryOperationsOptions {
  onDirectoryCreated?: (directory: Directory) => void;
}

/**
 * Hook that manages directory CRUD operations with both UI state and API mutation state.
 *
 * ## State Management Architecture
 *
 * This hook manages two types of state that serve different purposes:
 *
 * ### 1. UI State (`currentOperation`)
 * - **Purpose**: Tracks which directory is currently in an interactive UI mode
 * - **Examples**:
 *   - User clicked "Add directory" → shows input field
 *   - User clicked "Rename" → shows inline edit field
 *   - User clicked "Delete" → shows confirmation dialog
 * - **Lifetime**: From user action (e.g., clicking "edit") until completion or cancellation
 * - **Key Point**: This state exists BEFORE any API call is made
 *
 * ### 2. Query/Mutation State (from React Query)
 * - **Purpose**: Tracks the status of API calls (pending, error, success)
 * - **Properties**:
 *   - `isPending`: API request is in flight
 *   - `isError`: API request failed
 *   - `error`: Error details from failed request
 * - **Lifetime**: From API call start until response received
 * - **Key Point**: This state only exists during and after API calls
 *
 * ### Why Both Are Needed
 *
 * 1. **UI State enables user interaction**
 *    - Show/hide input fields
 *    - Enable/disable buttons
 *    - Track which specific directory is being edited
 *
 * 2. **Query State enables loading/error feedback**
 *    - Show loading spinners during API calls
 *    - Display error messages when operations fail
 *    - Handle optimistic updates and rollbacks
 *
 * ### Example Flow: Creating a Directory
 *
 * 1. User clicks "Add directory" → `startCreating()` sets UI state
 * 2. Input field appears (controlled by UI state)
 * 3. User types name and presses Enter → `createDirectory()` called
 * 4. API mutation starts → `isPending = true` (query state)
 * 5. During API call: input disabled, spinner shows (query state)
 * 6. API succeeds → UI state cleared, input hidden, success feedback
 * 7. API fails → Error shown (query state), input remains (UI state) for retry
 *
 * @param options - Configuration options including success callbacks
 * @returns Object containing operation functions and state checkers
 */
export function useDirectoryOperations(options?: UseDirectoryOperationsOptions) {
  // UI State - Tracks which directory is in interactive mode
  const [currentOperation, setCurrentOperation] = useState<DirectoryOperation | null>(null);

  const createMutation = useCreateDirectory({
    onSuccess: (directory: Directory) => {
      setCurrentOperation(null);
      options?.onDirectoryCreated?.(directory);
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

  /**
   * Enters "create mode" for a new directory at the specified parent level.
   * This shows the input field in the UI but doesn't make any API calls yet.
   *
   * @param parentId - Parent directory ID, or null for root level
   */
  const startCreating = (parentId: string | null) => {
    setCurrentOperation({ type: "create", parentId });
  };

  /**
   * Submits the create request to the API.
   * This is typically called when the user presses Enter in the input field.
   *
   * @param name - Name for the new directory
   * @param parentId - Parent directory ID, or null for root level
   */
  const createDirectory = (name: string, parentId: string | null) => {
    createMutation.mutate({ name, parentId });
  };

  /**
   * Checks if the UI is currently in "create mode" for a specific parent.
   * Use this to conditionally render the input field.
   *
   * @param parentId - Parent directory ID to check
   * @returns true if currently creating a directory under this parent
   */
  const isCreating = (parentId: string | null) => {
    return currentOperation?.type === "create" && currentOperation.parentId === parentId;
  };

  ////////////////////////////////////////////////////////////////
  // Update operations
  ////////////////////////////////////////////////////////////////

  /**
   * Enters "update mode" for the specified directory.
   * This shows the inline edit field in the UI but doesn't make any API calls yet.
   *
   * @param directoryId - ID of the directory to rename
   */
  const startUpdating = (directoryId: string) => {
    setCurrentOperation({ type: "update", directoryId });
  };

  /**
   * Submits the update request to the API.
   * This is typically called when the user presses Enter in the edit field.
   *
   * @param directoryId - ID of the directory to update
   * @param name - New name for the directory
   * @param parentId - Parent directory ID (for potential moves in the future)
   */
  const updateDirectory = (directoryId: string, name: string, parentId: string | null) => {
    updateMutation.mutate({ id: directoryId, data: { name, parentId } });
  };

  /**
   * Checks if the UI is currently in "update mode" for a specific directory.
   * Use this to conditionally render the inline edit field.
   *
   * @param directoryId - Directory ID to check
   * @returns true if currently editing this directory
   */
  const isUpdating = (directoryId: string) => {
    return currentOperation?.type === "update" && currentOperation.directoryId === directoryId;
  };

  ////////////////////////////////////////////////////////////////
  // Delete operations
  ////////////////////////////////////////////////////////////////

  /**
   * Enters "delete mode" for the specified directory.
   * This typically shows a confirmation dialog but doesn't make any API calls yet.
   *
   * @param directoryId - ID of the directory to delete
   */
  const startDeleting = (directoryId: string) => {
    setCurrentOperation({ type: "delete", directoryId });
  };

  /**
   * Submits the delete request to the API.
   * This is typically called when the user confirms deletion in a dialog.
   *
   * @param directoryId - ID of the directory to delete
   * @param allDirectories - Complete list of directories (used for optimistic updates)
   */
  const deleteDirectory = (directoryId: string, allDirectories: Directory[]) => {
    deleteMutation.mutate({ directoryId, allDirectories });
  };

  /**
   * Checks if the UI is currently in "delete mode" for a specific directory.
   * Use this to conditionally render the delete confirmation dialog.
   *
   * @param directoryId - Directory ID to check
   * @returns true if currently deleting this directory
   */
  const isDeleting = (directoryId: string) => {
    return currentOperation?.type === "delete" && currentOperation.directoryId === directoryId;
  };

  ////////////////////////////////////////////////////////////////
  // Shared operations
  ////////////////////////////////////////////////////////////////

  /**
   * Exits the current operation mode without making any API calls.
   * This is typically called when the user presses Escape or clicks Cancel.
   */
  const cancelOperation = () => {
    setCurrentOperation(null);
  };

  ////////////////////////////////////////////////////////////////
  // Return - Organized by operation type
  ////////////////////////////////////////////////////////////////

  return {
    // Create Operations
    create: {
      start: startCreating,
      execute: createDirectory,
      isActive: isCreating,
      isPending: createMutation.isPending,
      isError: createMutation.isError,
      error: createMutation.error,
    },

    // Update Operations
    update: {
      start: startUpdating,
      execute: updateDirectory,
      isActive: isUpdating,
      isPending: updateMutation.isPending,
      isError: updateMutation.isError,
      error: updateMutation.error,
    },

    // Delete Operations
    delete: {
      start: startDeleting,
      execute: deleteDirectory,
      isActive: isDeleting,
      isPending: deleteMutation.isPending,
      isError: deleteMutation.isError,
      error: deleteMutation.error,
    },

    // Shared Operations
    cancel: cancelOperation,
  };
}
