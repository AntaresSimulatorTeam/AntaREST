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

import type { Directory } from "@/services/api/directories/types";
import type { StudyFolder } from "@/redux/ducks/studies";

export const DIRECTORIES: Directory[] = [
  { id: "other", name: "Other", parentId: null },
  { id: "keep", name: "Keep", parentId: "other" },
  { id: "parent", name: "Parent", parentId: null },
  { id: "target", name: "Target", parentId: "parent" },
  { id: "child", name: "Child", parentId: "target" },
];

export const TARGET_FOLDER = {
  tree: "managed",
  directoryId: "target",
  directoryIds: ["target", "child"],
} satisfies StudyFolder;
