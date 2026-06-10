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

import { toSemanticVersion } from "@/utils/versionUtils";
import z from "zod";

const studyTypeSchema = z.enum(["variantstudy", "rawstudy"]);

const studyOwnerSchema = z.object({
  id: z.int().nullable(),
  name: z.string(),
});

const studyGroupSchema = z.object({
  id: z.string(),
  name: z.string(),
});

const studyPublicModeSchema = z.enum(["NONE", "READ", "EXECUTE", "EDIT", "FULL"]);

export const studySchema = z
  .object({
    id: z.string(),
    name: z.string(),
    version: z.string().transform(toSemanticVersion),
    author: z.string().nullable(),
    editor: z.string().nullable(),
    created: z.string(),
    updated: z.string(),
    type: studyTypeSchema,
    owner: studyOwnerSchema,
    groups: z.array(studyGroupSchema),
    public_mode: studyPublicModeSchema,
    workspace: z.string(),
    managed: z.boolean(),
    archived: z.boolean(),
    horizon: z.string().nullable(),
    folder: z.string().nullable(),
    tags: z.array(z.string()),
    directory_id: z.string().nullable(),
    parent_id: z.string().nullable(),
  })
  .transform(
    ({
      created,
      updated,
      public_mode: publicMode,
      directory_id: directoryId,
      parent_id: parentId,
      ...rest
    }) => ({
      ...rest,
      creationDate: created,
      modificationDate: updated,
      publicMode,
      directoryId,
      parentId,
    }),
  );

export const studyVersionsSchema = z
  .array(z.string())
  .transform((versions) => versions.map(toSemanticVersion));
