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
 * Directory tree node with hierarchical structure
 * Built from flat Directory[] using parentId relationships
 */
export interface DirectoryTreeNode {
  id: string;
  name: string;
  path: string; // Using ID as path for consistency with tree navigation
  parentId: string | null;
  children: DirectoryTreeNode[];
}

/**
 * Props for ManagedTreeNode component
 */
export interface ManagedTreeNodeProps {
  node: DirectoryTreeNode;
  onNodeClick: (id: string) => void;
  selectedPath?: string;
}

/**
 * Props for ManagedTree component
 */
export interface ManagedTreeProps {
  studies: StudyMetadata[];
  onNodeClick: (id: string) => void;
}
