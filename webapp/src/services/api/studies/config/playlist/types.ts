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

// eslint-disable-next-line @typescript-eslint/consistent-type-definitions
export type Playlist = {
  status: boolean;
  weight: number;
};

export type PlaylistData = Record<string, Playlist>;

export interface SetPlaylistDataParams {
  studyId: StudyMetadata["id"];
  data: PlaylistData;
}
