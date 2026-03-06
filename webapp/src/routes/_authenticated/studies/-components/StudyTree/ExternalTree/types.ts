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

export interface ExternalTreeNodeMetadata {
  name: string;
  path: string;
  children: ExternalTreeNodeMetadata[];
  hasChildren?: boolean;
  isStudyFolder?: boolean;
  isScannedStudy?: boolean;
  alias?: string;
}

export interface ExternalTreeNodeProps {
  node: ExternalTreeNodeMetadata;
  itemsLoading: string[];
  exploredFolders: string[];
}

export interface ExternalTreeProps {
  studies: StudyMetadata[];
  onRootClick: () => void;
}
