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
import { outputsSchema } from "./schemas";
import type { GetOutputsParams, Output, OutputParams } from "./types";

export async function getOutputs({ studyId }: GetOutputsParams): Promise<Output[]> {
  const { data } = await client.get(`/v1/studies/${studyId}/outputs`);
  return outputsSchema.parse(data);
}

export async function deleteOutput({ studyId, outputId }: OutputParams) {
  await client.delete(`/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}`);
}

export async function archiveOutput({ studyId, outputId }: OutputParams) {
  const { data: taskId } = await client.post(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/_archive`,
  );
  return z.string().parse(taskId);
}

export async function unarchiveOutput({ studyId, outputId }: OutputParams) {
  const { data: taskId } = await client.post(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/_unarchive`,
  );
  return z.string().parse(taskId);
}
