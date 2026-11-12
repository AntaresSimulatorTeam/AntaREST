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

import { createStudy } from "@/tests/studyFixtures";

export function externalStudy(folder: string) {
  return createStudy({ id: folder, folder, workspace: "workspace", managed: false });
}

export function folder(name: string, parentPath: string) {
  return {
    name,
    path: [parentPath.replace(/^\/workspace\/?/, ""), name].filter(Boolean).join("/"),
    parentPath,
    workspace: "workspace",
    hasChildren: true,
  };
}

export const FOLDERS_BY_PATH: Record<string, Array<ReturnType<typeof folder>>> = {
  "": [folder("Projects", "/workspace")],
  Projects: [folder("Target", "/workspace/Projects")],
  "Projects/Target": [folder("Child", "/workspace/Projects/Target")],
};
