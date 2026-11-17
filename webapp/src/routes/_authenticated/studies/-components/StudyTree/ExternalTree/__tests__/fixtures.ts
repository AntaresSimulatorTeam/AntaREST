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

import type { FolderDTO } from "@/queries/explorer/schemas";
import { createStudy } from "@/tests/studyFixtures";
import type { StudyMetadata } from "@/types/types";

export const WORKSPACE = { name: "workspace", diskName: "" };

export const DISK_USAGE = { totalBytes: 100, usedBytes: 40, freeBytes: 60 };

export const FULL_DISK_USAGE = { totalBytes: 100, usedBytes: 90, freeBytes: 10 };

export function externalStudy(folder: string, overrides: Partial<StudyMetadata> = {}) {
  return createStudy({
    id: folder,
    folder,
    workspace: WORKSPACE.name,
    managed: false,
    ...overrides,
  });
}

export function folder(name: string, parentPath: string): FolderDTO {
  return {
    name,
    path: [parentPath.replace(/^\/workspace\/?/, ""), name].filter(Boolean).join("/"),
    parentPath,
    workspace: WORKSPACE.name,
    hasChildren: true,
  };
}

export const FOLDERS_BY_PATH: Record<string, Array<ReturnType<typeof folder>>> = {
  "": [folder("Projects", "/workspace")],
  Projects: [folder("Target", "/workspace/Projects")],
  "Projects/Target": [folder("Child", "/workspace/Projects/Target")],
};
