/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

export interface StudyTreeNodeMetadata {
  name: string;
  path: string;
  children: StudyTreeNodeMetadata[];
  hasChildren?: boolean;
  isStudyFolder?: boolean;
  isScannedStudy?: boolean;
  alias?: string;
}

export interface FolderDTO {
  name: string;
  path: string;
  workspace: string;
  parentPath: string;
  hasChildren?: boolean;
  isStudyFolder?: boolean;
}

export interface WorkspaceDTO {
  name: string;
  diskName: string;
}

export interface StudyTreeNodeProps {
  node: StudyTreeNodeMetadata;
  itemsLoading: string[];
  onNodeClick: (id: string) => void;
  exploredFolders: string[];
}
