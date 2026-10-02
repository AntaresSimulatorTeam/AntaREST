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

import { format } from "@/utils/stringUtils";
import client from "../../client";
import { userResourcesTreeSchema } from "./schemas";
import type {
  CreateOrReplaceUserResourceParams,
  DeleteUserResourceParams,
  GetUserResourceContentParams,
  GetUserResourceTreeParams,
  UserResourcesTree,
} from "./types";

const BASE_URL = "/v1/studies/{studyId}/user-resources";

/**
 * GET /v1/studies/{studyId}/user-resources - Gets the tree of user resources for the specified study.
 *
 * @param params - Parameters.
 * @param params.studyId - The ID of the study.
 * @returns The tree of user resources for the specified study.
 */
export async function getUserResourcesTree({
  studyId,
}: GetUserResourceTreeParams): Promise<UserResourcesTree> {
  const { data } = await client.get(format(BASE_URL, { studyId }));
  return userResourcesTreeSchema.parse(data);
}

/**
 * GET /v1/studies/{studyId}/user-resources/content - Gets the content of a user resource
 * for the specified study.
 *
 * @param params - Parameters.
 * @param params.studyId - The ID of the study.
 * @param params.path - The path of the user resource.
 * @returns The content of the user resource.
 */
export async function getUserResourceContent({ studyId, path }: GetUserResourceContentParams) {
  const { data } = await client.get<Blob>(format(`${BASE_URL}/content`, { studyId }), {
    params: { path },
    responseType: "blob",
  });
  return data;
}

/**
 * PUT /v1/studies/{studyId}/user-resources - Creates or replaces a user resource
 * for the specified study.
 *
 * @param params - Parameters.
 * @param params.studyId - The ID of the study.
 * @param params.path - The path of the user resource.
 * @param params.resourceType - The type of the user resource.
 * @param params.file - The file to upload if the resource type is "file".
 */
export async function createOrReplaceUserResource({
  studyId,
  path,
  resourceType,
  file,
}: CreateOrReplaceUserResourceParams) {
  const url = format(BASE_URL, { studyId });
  const body = resourceType === "file" ? { file } : {};

  await client.putForm(url, body, {
    params: { path, resource_type: resourceType },
  });
}

export async function deleteUserResource({ studyId, path }: DeleteUserResourceParams) {
  await client.delete(format(BASE_URL, { studyId }), {
    params: { path },
  });
}
