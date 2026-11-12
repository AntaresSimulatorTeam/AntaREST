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

import { StorageMode, StudyType, type StudyMetadata } from "@/types/types";

export function createStudy(overrides: Partial<StudyMetadata> = {}): StudyMetadata {
  return {
    id: "study",
    name: "Study",
    creationDate: "2026-11-05",
    modificationDate: "2026-11-05",
    owner: { id: 1, name: "Owner" },
    editor: "Editor",
    author: "Author",
    type: StudyType.RAW,
    version: "9.3",
    workspace: "network",
    managed: true,
    archived: false,
    storageMode: StorageMode.FILESYSTEM,
    groups: [],
    publicMode: "NONE",
    directoryId: null,
    ...overrides,
  };
}
