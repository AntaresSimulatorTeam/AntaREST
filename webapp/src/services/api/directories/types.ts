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

import type { z } from "zod";
import type {
  createDirectoryParamsSchema,
  directorySchema,
  updateDirectoryParamsSchema,
} from "./schemas";

export type Directory = z.infer<typeof directorySchema>;
export type CreateDirectoryParams = z.infer<typeof createDirectoryParamsSchema>;
export type UpdateDirectoryParams = z.infer<typeof updateDirectoryParamsSchema>;
