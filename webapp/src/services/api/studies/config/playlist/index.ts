/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type { StudyMetadata } from "@/types/types";
import client from "@/services/api/client";
import { format } from "@/utils/stringUtils";
import type { PlaylistData, SetPlaylistDataParams } from "./types";

const URL = "/v1/studies/{studyId}/config/playlist/form";

export async function getPlaylistData(params: { studyId: StudyMetadata["id"] }) {
  const url = format(URL, { studyId: params.studyId });
  const { data } = await client.get<PlaylistData>(url);
  return data;
}

export async function setPlaylistData({ studyId, data }: SetPlaylistDataParams) {
  const url = format(URL, { studyId });
  await client.put(url, data);
}
