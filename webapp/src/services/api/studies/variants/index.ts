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
import client from "../../client";
import { variantTreeSchema } from "./schemas";
import type { CreateVariantParams, GetVariantTreeParams } from "./types";

export async function getVariantTree({ studyId, fromRoot = true }: GetVariantTreeParams) {
  const { data } = await client.get(`/v1/studies/${studyId}/variants`, {
    params: { from_root: fromRoot },
  });
  return variantTreeSchema.parse(data);
}

export async function createVariant({ studyId, name }: CreateVariantParams) {
  const { data } = await client.post(`/v1/studies/${studyId}/variants`, null, {
    params: { name },
  });

  return z.string().parse(data);
}
