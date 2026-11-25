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

import type { StudyFolder } from "@/redux/ducks/studies";
import type { Directory } from "@/services/api/directories/types";
import type { Favorite } from "../types";

export const FAVORITE_STUDY: Favorite = {
  id: "study-study-id",
  name: "Favorite study",
  type: "study",
  original: { studyId: "study-id", studyName: "Favorite study" },
};

export const DIRECTORIES: Directory[] = [
  { id: "folder", name: "Folder", parentId: null },
  { id: "child", name: "Child", parentId: "folder" },
];

export const FOLDER_CASES = [
  {
    favorite: {
      id: "directory-folder",
      name: "Favorite folder",
      type: "directory",
      original: { directoryId: "folder", directoryName: "Favorite folder" },
    },
    target: { tree: "managed", directoryId: "folder", directoryIds: ["folder", "child"] },
  },
  {
    favorite: {
      id: "external-directory-folder",
      name: "External folder",
      type: "externalDirectory",
      absolutePath: "/external/folder",
      original: { workspace: "external", path: "folder" },
    },
    target: { tree: "external", path: "/external/folder" },
  },
] satisfies Array<{ favorite: Favorite; target: StudyFolder }>;
