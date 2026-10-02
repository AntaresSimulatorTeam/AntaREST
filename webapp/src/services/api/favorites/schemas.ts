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

export const favoriteStudySchema = z.object({
  studyId: z.string(),
  studyName: z.string(),
});

export const favoriteDirectorySchema = z.object({
  directoryId: z.string(),
  directoryName: z.string(),
});

export const favoriteExternalDirectorySchema = z.object({
  workspace: z.string().min(1),
  path: z.string().min(1),
});
