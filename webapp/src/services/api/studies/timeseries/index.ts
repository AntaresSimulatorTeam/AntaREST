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

import type { SetTimeSeriesConfigParams } from "@/services/api/studies/timeseries/types";
import type { StudyMetadata } from "@/types/types";
import * as R from "ramda";
import client from "../../client";

/**
 * Launches time series generation task for the specified study.
 *
 * @param params - The parameters.
 * @param params.studyId - The study ID.
 * @param params.outageDetails - Whether to generate outage details.
 * @returns A promise that returns the task ID if fulfilled.
 */
export async function generateTimeSeries(params: {
  studyId: StudyMetadata["id"];
  outageDetails?: boolean;
}) {
  const { data } = await client.put<string>(
    `/v1/studies/${params.studyId}/timeseries/generate`,
    null,
    { params: { outage_details: params.outageDetails ?? false } },
  );
  return data;
}

export async function setTimeSeriesConfig({ studyId, values }: SetTimeSeriesConfigParams) {
  // Extra fields not allowed by the API
  const validDTO = R.map((config = {}) => R.pick(["number"], config), values);

  await client.put(`/v1/studies/${studyId}/timeseries/config`, validDTO);
}
