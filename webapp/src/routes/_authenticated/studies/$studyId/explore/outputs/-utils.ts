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

import { taskQueries } from "@/queries/tasks/queries";
import type { Job } from "@/services/api/launcher/jobs/types";
import type { Output } from "@/services/api/studies/outputs/types";
import { TaskStatus } from "@/services/api/tasks/constants";
import type { Task } from "@/services/api/tasks/types";
import { isTaskFinished } from "@/services/api/tasks/utils";
import type { QueryClient } from "@tanstack/react-query";
import { compareDesc, parseISO, secondsToMilliseconds } from "date-fns";

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

export async function waitForOutputArchiveTask(client: QueryClient, taskId: Task["id"]) {
  const taskQuery = { ...taskQueries.detail(taskId), staleTime: 0, retry: 2 };

  // A fast archive can send its completion event before the browser starts listening.
  // Waiting for that WebSocket event would leave the output disabled forever. A status
  // request still tells us the archive finished, even if we missed the event.
  let task = await client.fetchQuery(taskQuery);

  // Pending and Running are successful responses. If the task gets stuck, the retry limit
  // never applies and the output's actions stay disabled.
  //
  // TODO: Give polling an overall deadline. On expiry, refresh the output list
  // and show "Couldn't confirm completion". Keep the task ID so the user can check again.
  // The archive can still finish on the server after the browser stops waiting.
  while (!isTaskFinished(task)) {
    await new Promise((resolve) => setTimeout(resolve, secondsToMilliseconds(2)));
    task = await client.fetchQuery(taskQuery);
  }

  if (task.status !== TaskStatus.Completed) {
    throw new Error(task.result?.message || task.name);
  }
}
