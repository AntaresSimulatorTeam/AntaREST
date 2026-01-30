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

import type { StudyMetadata } from "@/types/types";

/**
 * Represents a node in the directory tree structure
 */
export interface DirectoryTreeNode {
  id: string;
  name: string;
  path: string; // Using ID as path for consistency with tree navigation
  parentId: string | null; // null = root level directory, string = subdirectory
  children: DirectoryTreeNode[];
}

/**
 * Props for the ManagedTreeNode component
 * Handles rendering of individual tree nodes with CRUD operations
 */
export interface ManagedTreeNodeProps {
  node: DirectoryTreeNode;
  onNodeClick: (id: string) => void;
  selectedPath?: string;

  // Create handlers
  // Note: parentId represents where the folder will be created
  // - For root folders: parentId is null (handled in ManagedTree)
  // - For subfolders: parentId is the directory ID that will contain the new folder
  onAddSubFolder: (parentId: string) => void;
  onSaveSubFolder: (parentId: string) => (name: string) => void;
  onCancelSubFolder: () => void;
  isCreatingSubFolder: (parentId: string) => boolean;

  // Update handlers
  onStartUpdate: (directoryId: string) => void;
  onSaveUpdate: (directoryId: string, name: string, parentId: string | null) => void;
  onCancelUpdate: () => void;
  isUpdating: (directoryId: string) => boolean;

  // Delete handlers
  onDelete: (directoryId: string) => void;
  isDeleting: (directoryId: string) => boolean;
}

/**
 * Props for the main ManagedTree component
 */
export interface ManagedTreeProps {
  studies: StudyMetadata[];
  isCreatingFolder: boolean;
  onFolderCreated: () => void;
  onHomeClick: () => void;
}
