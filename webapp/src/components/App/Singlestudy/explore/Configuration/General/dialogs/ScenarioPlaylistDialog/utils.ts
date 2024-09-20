/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

interface PlaylistColumns extends Record<string, boolean | number> {
  status: boolean;
  weight: number;
}

export type PlaylistData = Record<number, PlaylistColumns>;

export const DEFAULT_WEIGHT = 1;

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/playlist/form`;
}

export async function getPlaylist(
  studyId: StudyMetadata["id"],
): Promise<PlaylistData> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setPlaylist(
  studyId: StudyMetadata["id"],
  data: PlaylistData,
): Promise<void> {
  return client.put(makeRequestURL(studyId), data);
}
