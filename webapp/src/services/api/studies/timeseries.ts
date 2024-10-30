/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { StudyMetadata } from "../../../common/types";
import client from "../client";

/**
 * Launches time series generation task for the specified study.
 *
 * @param params - The parameters.
 * @param params.studyId - The study ID.
 * @returns A promise that returns the task ID if fulfilled.
 */
export async function generateTimeSeries(params: {
  studyId: StudyMetadata["id"];
}) {
  const { data } = await client.put<string>(
    `v1/studies/${params.studyId}/timeseries/generate`,
  );
  return data;
}