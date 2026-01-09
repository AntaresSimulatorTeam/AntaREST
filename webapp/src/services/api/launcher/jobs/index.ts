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

import client from "../../client";
import { adaptJobDtoToJob } from "./adapters";
import type { GetJobsParams, JobDTO } from "./types";

const BASE_URL = "/v1/launcher/jobs";

export async function getJobs(params: GetJobsParams) {
  const queryParams =
    "studyId" in params
      ? { study: params.studyId }
      : {
          filter_orphans: params.filterOrphans,
          latest: params.latest,
        };

  const { data } = await client.get<JobDTO[]>(BASE_URL, { params: queryParams });

  return data.map(adaptJobDtoToJob);
}
