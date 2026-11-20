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

import client from "@/services/api/client";
import type { Task } from "@/services/api/tasks/types";
import { isAxiosError } from "axios";
import z from "zod";
import type { OutputParams } from "../types";
import { gemsViewsPreparationSchema, gemsViewsSchema } from "./schemas";
import type { GemsViewsState } from "./types";

/**
 * GET /v1/studies/{studyId}/outputs/{outputId}/gems-views - Reads the output's navigation metadata.
 *
 * @param params - Study and output identifiers.
 * @param params.studyId - Study identifier.
 * @param params.outputId - Output identifier.
 * @param signal - Cancels the request when the reader no longer needs it.
 * @returns Ready views (possibly empty), or the preparation state reported by the backend.
 * @throws If the metadata is invalid or the request fails, including ordinary 404 responses.
 */
export async function getGemsViews(
  { studyId, outputId }: OutputParams,
  signal?: AbortSignal,
): Promise<GemsViewsState> {
  try {
    const { data } = await client.get(
      `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/gems-views`,
      { signal },
    );

    return { status: "READY", views: gemsViewsSchema.parse(data) };
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 404) {
      const preparation = gemsViewsPreparationSchema.safeParse(error.response.data);

      if (preparation.success) {
        return preparation.data;
      }
    }

    throw error;
  }
}

/**
 * POST /v1/studies/{studyId}/outputs/{outputId}/gems-views/materialize - Prepares the metadata.
 *
 * @param params - Study and output identifiers.
 * @param params.studyId - Study identifier.
 * @param params.outputId - Output identifier.
 * @returns The task ID, or undefined if the backend reports the metadata is already ready (417).
 * @throws If the task ID is invalid or the request otherwise fails.
 */
export async function materializeGemsViews({
  studyId,
  outputId,
}: OutputParams): Promise<Task["id"] | undefined> {
  try {
    const { data } = await client.post(
      `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/gems-views/materialize`,
    );

    return z.string().min(1).parse(data);
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 417) {
      return undefined;
    }

    throw error;
  }
}
