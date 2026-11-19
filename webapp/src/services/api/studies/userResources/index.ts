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

import { getFileContent } from "@/services/api/files";
import { filesTreeSchema } from "@/services/api/files/schemas";
import type { FilesTree } from "@/services/api/files/types";
import client from "../../client";
import type {
  CreateOrReplaceUserResourceParams,
  DeleteUserResourceParams,
  GetUserResourceContentParams,
  GetUserResourceTreeParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/user-resources - Gets the tree of user resources for the specified study.
 *
 * @param params - Parameters.
 * @param params.studyId - The ID of the study.
 * @returns The tree of user resources for the specified study.
 * @throws If the response does not match the file-tree schema.
 */
export async function getUserResourcesTree({
  studyId,
}: GetUserResourceTreeParams): Promise<FilesTree> {
  const { data } = await client.get(`/v1/studies/${studyId}/user-resources`);

  return filesTreeSchema.parse(data);
}

/**
 * GET /v1/studies/{studyId}/user-resources/content - Gets the content of a user resource
 * for the specified study.
 *
 * @param params - Parameters.
 * @param params.studyId - The ID of the study.
 * @param params.path - The path of the user resource.
 * @returns The content of the user resource.
 * @throws If the request fails or the response is not a Blob.
 */
export function getUserResourceContent({ studyId, path }: GetUserResourceContentParams) {
  return getFileContent(`/v1/studies/${studyId}/user-resources/content`, path);
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
  const body = resourceType === "file" ? { file } : {};

  await client.putForm(`/v1/studies/${studyId}/user-resources`, body, {
    params: { path, resource_type: resourceType },
  });
}

/**
 * DELETE /v1/studies/{studyId}/user-resources - Deletes a file or folder.
 *
 * @param params - Resource to delete.
 * @param params.studyId - Study identifier.
 * @param params.path - Path relative to the study's User Resources folder.
 */
export async function deleteUserResource({ studyId, path }: DeleteUserResourceParams) {
  await client.delete(`/v1/studies/${studyId}/user-resources`, {
    params: { path },
  });
}
