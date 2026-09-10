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

import type z from "zod";
import type { Study } from "../types";
import type { userResourcesTreeSchema, userResourceTypeSchema } from "./schemas";

type UserResourceType = z.infer<typeof userResourceTypeSchema>;

////////////////////////////////////////////////////////////////
// Response Types
////////////////////////////////////////////////////////////////

export type UserResourcesTree = z.infer<typeof userResourcesTreeSchema>;

////////////////////////////////////////////////////////////////
// Request Params
////////////////////////////////////////////////////////////////

export interface GetUserResourceContentParams {
  studyId: Study["id"];
  path: string;
}

export interface DeleteUserResourceParams {
  studyId: Study["id"];
  path: string;
}

interface CreateOrReplaceUserResourceBaseParams<T extends UserResourceType> {
  studyId: Study["id"];
  path: string;
  resourceType: T;
}

export type CreateOrReplaceUserResourceParams =
  | (CreateOrReplaceUserResourceBaseParams<"file"> & {
      file: File;
    })
  | (CreateOrReplaceUserResourceBaseParams<"folder"> & {
      file?: never;
    });
