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
import type { Study } from "../types";
import { userResourcesTreeSchema } from "./schemas";
import type {
  CreateOrReplaceUserResourceParams,
  DeleteUserResourceParams,
  GetUserResourceContentParams,
} from "./types";

const BASE_URL = "/v1/studies/{studyId}/user-resources";

export async function getUserResourcesTree({ studyId }: { studyId: Study["id"] }) {
  const { data } = await client.get(format(BASE_URL, { studyId }));
  return userResourcesTreeSchema.parse(data);
}

export async function getUserResourceContent({ studyId, path }: GetUserResourceContentParams) {
  const { data } = await client.get(format(`${BASE_URL}/content`, { studyId }), {
    params: { path },
  });
  return data;
}

export async function createOrReplaceUserResource({
  studyId,
  path,
  resourceType,
  file,
}: CreateOrReplaceUserResourceParams) {
  const url = format(BASE_URL, { studyId });
  const body = { file };

  await client.putForm(url, body, {
    params: { path, resource_type: resourceType },
  });
}

export async function deleteUserResource({ studyId, path }: DeleteUserResourceParams) {
  await client.delete(format(BASE_URL, { studyId }), {
    params: { path },
  });
}
