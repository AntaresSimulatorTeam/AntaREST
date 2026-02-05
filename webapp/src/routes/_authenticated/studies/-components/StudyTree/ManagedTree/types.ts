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

export interface DirectoryTreeNode {
  id: string;
  name: string;
  path: string; // Using ID as path for consistency with tree navigation
  parentId: string | null; // null = root level directory, string = subdirectory
  children: DirectoryTreeNode[];
}

export interface ManagedTreeNodeProps {
  node: DirectoryTreeNode;
  onNodeClick: (id: string) => void;
  selectedPath?: string;

  // Create handlers
  // Note: parentId represents where the directory will be created
  // - For root directories: parentId is null (handled in ManagedTree)
  // - For subdirectories: parentId is the directory ID that will contain the new directory
  onAddSubDirectory: (parentId: string) => void;
  onSaveSubDirectory: (parentId: string) => (name: string) => void;
  onCancelSubDirectory: () => void;
  isCreatingSubDirectory: (parentId: string) => boolean;
  isCreatePending: boolean;

  // Update handlers
  onStartUpdate: (directoryId: string) => void;
  onSaveUpdate: (directoryId: string, name: string, parentId: string | null) => void;
  onCancelUpdate: () => void;
  isUpdating: (directoryId: string) => boolean;
  isUpdatePending: boolean;

  // Delete handlers
  onDelete: (directoryId: string) => void;
  isDeleting: (directoryId: string) => boolean;
  isDeletePending: boolean;
}

export interface ManagedTreeProps {
  //studies: StudyMetadata[];
  isCreatingDirectory: boolean;
  onDirectoryCreated: () => void;
  onRootClick: () => void;
}
