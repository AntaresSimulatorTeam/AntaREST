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
import { studySchema } from "../schemas";
import type { Study } from "../types";
import { variantTreeSchema } from "./schemas";
import type { CreateVariantParams } from "./types";

export async function getVariantTree({ studyId }: { studyId: Study["id"] }) {
  const { data } = await client.get(`/v1/studies/${studyId}/variants`);
  return variantTreeSchema.parse(data);
}

export const getVariantParents = async ({ studyId }: { studyId: Study["id"] }) => {
  const { data } = await client.get(`/v1/studies/${studyId}/parents`);
  return z.array(studySchema).parse(data);
};

export const getVariantDirectParent = async ({ studyId }: { studyId: Study["id"] }) => {
  const { data } = await client.get(`/v1/studies/${studyId}/parents`, {
    params: { direct: true },
  });

  return data ? studySchema.parse(data) : null;
};

export async function getVariantLatestParent({ studyId }: { studyId: Study["id"] }) {
  const parents = await getVariantParents({ studyId });
  const latestVariant = parents.length > 0 ? parents[parents.length - 1] : null;

  return latestVariant ? studySchema.parse(latestVariant) : null;
}

export const createVariant = async ({ studyId, name }: CreateVariantParams) => {
  const { data } = await client.post(`/v1/studies/${studyId}/variants`, null, {
    params: { name },
  });

  return z.string().parse(data);
};
