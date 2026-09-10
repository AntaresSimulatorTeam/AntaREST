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

import z from "zod";

export const userResourceTypeSchema = z.enum(["file", "folder"]);

export const userResourceFolderSchema = z.object({
  name: z.string(),
  files: z.array(z.string()),
  get directories() {
    return z.array(userResourceFolderSchema);
  },
});

export const userResourcesTreeSchema = z.object({
  files: z.array(z.string()),
  directories: z.array(userResourceFolderSchema),
});
