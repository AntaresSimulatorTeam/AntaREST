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

import type { Study } from "@/services/api/studies/types";
import { studyKeys } from "../studies/keys";

export const outputKeys = {
  all: () => [...studyKeys.all(), "outputs"] as const,
  list: (studyId: Study["id"]) => [...outputKeys.all(), { studyId }] as const,
  delete: (studyId: Study["id"]) => [...outputKeys.list(studyId), "deleteOutput"] as const,
  archive: (studyId: Study["id"]) => [...outputKeys.list(studyId), "archiveOutput"] as const,
  unarchive: (studyId: Study["id"]) => [...outputKeys.list(studyId), "unarchiveOutput"] as const,
};
