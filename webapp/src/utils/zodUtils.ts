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

/**
 * Wraps a Zod schema to accept `null` or `undefined` as input and normalize
 * both to `undefined` in the output.
 *
 * This is useful when an API may return `null` for absent fields, but the
 * frontend treats absence uniformly as `undefined` — aligning with TypeScript's
 * optional field convention (`field?: T`) and avoiding dual null/undefined checks
 * throughout the codebase.
 *
 * @example
 * const schema = z.object({
 *   progress: nullishToOptional(z.number()),  // number | null → number | undefined
 * });
 *
 * schema.parse({ progress: null })      // => { progress: undefined }
 * schema.parse({ progress: 42 })        // => { progress: 42 }
 * schema.parse({})                      // => { progress: undefined }
 */
export function nullishToOptional<T extends z.ZodTypeAny>(schema: T) {
  return schema.nullish().transform((v) => v ?? undefined);
}
