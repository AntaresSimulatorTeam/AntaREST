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

export interface StudyTreeNode {
  name: string;
  path: string;
  children: StudyTreeNode[];
  hasChildren?: boolean;
}

export interface NonStudyFolderDTO {
  name: string;
  path: string;
  workspace: string;
  parentPath: string;
  hasChildren?: boolean;
}

export interface StudyTreeNodeProps {
  studyTreeNode: StudyTreeNode;
  parentId: string;
  itemsLoading: string[];
  onNodeClick: (id: string) => void;
}
