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

import type { Job } from "@/services/api/launcher/jobs/types";
import type { Output } from "@/services/api/studies/outputs/types";
import { compareDesc, parseISO } from "date-fns";

export type OutputWithJob = Output & {
  job?: Job;
};

export function sortJobsByCreationDate(jobs: Job[]) {
  // Most recent first
  return [...jobs].sort((a, b) => compareDesc(parseISO(a.creationDate), parseISO(b.creationDate)));
}

export function sortOutputsByCompletionDate(outputs: OutputWithJob[]) {
  // Most recent first
  return [...outputs].sort((a, b) => {
    const dateA = a.job?.completionDate;
    const dateB = b.job?.completionDate;

    if (!dateA || !dateB) {
      // Consider the one with a date as more recent, or equal if both don't have a date
      return dateA ? -1 : dateB ? 1 : 0;
    }

    return compareDesc(parseISO(dateA), parseISO(dateB));
  });
}

export function selectJobsData(jobs: Job[]) {
  const jobsByOutputId = jobs.reduce(
    (acc, job) => {
      if (job.outputId) {
        acc[job.outputId] = job;
      }
      return acc;
    },
    {} as Record<NonNullable<Job["outputId"]>, Job>,
  );

  const runningJobs = sortJobsByCreationDate(jobs.filter((job) => job.status === "running"));

  return { jobsByOutputId, runningJobs };
}
