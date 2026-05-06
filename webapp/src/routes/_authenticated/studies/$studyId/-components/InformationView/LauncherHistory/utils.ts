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

import { getJobProgress } from "@/services/api/launcher";
import type { Job } from "@/services/api/launcher/jobs/types";
import type { JobsProgressById } from "@/types/types";
import moment from "moment";

export function sortJobs(jobs: Job[]) {
  return [...jobs].sort((j1, j2) => {
    const defaultCompletionDate = moment();
    const j1CompletionDate = j1.completionDate || defaultCompletionDate;
    const j2CompletionDate = j2.completionDate || defaultCompletionDate;
    if (j1CompletionDate === j2CompletionDate) {
      return moment(j1.creationDate).isAfter(moment(j2.creationDate)) ? -1 : 1;
    }
    return moment(j1CompletionDate).isAfter(moment(j2CompletionDate)) ? -1 : 1;
  });
}

export async function getJobsProgressById(jobs: Job[]): Promise<JobsProgressById> {
  const runningJobs = jobs.filter((job) => job.status === "running");

  const entries = await Promise.all(
    runningJobs.map(async ({ id }) => [id, await getJobProgress({ id })] as const),
  );

  return Object.fromEntries(entries);
}
