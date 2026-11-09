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

import { z } from "zod";

const byteCountSchema = z.number().int().nonnegative();

export const workspaceDiskUsageSchema = z
  .object({
    // The backend returns zero when the filesystem is unavailable.
    total_bytes: byteCountSchema.positive(),
    used_bytes: byteCountSchema,
    free_bytes: byteCountSchema,
  })
  .transform(({ total_bytes: totalBytes, used_bytes: usedBytes, free_bytes: freeBytes }) => ({
    totalBytes,
    usedBytes,
    freeBytes,
  }));
