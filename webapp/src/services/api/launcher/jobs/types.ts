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

import type { LauncherParamsDTO } from "../types";

export type JobStatus = "pending" | "failed" | "success" | "running";

export interface JobUserInfo {
  id: string;
  name: string;
}

export interface JobDTO {
  id: string;
  study_id: string;
  launcher?: string;
  launcher_params?: string;
  status: JobStatus;
  creation_date: string;
  completion_date?: string;
  msg?: string;
  output_id?: string;
  exit_code?: number;
  solver_stats?: string;
  owner?: JobUserInfo;
}

export interface Job {
  id: string;
  studyId: string;
  launcher?: string;
  launcherParams?: LauncherParamsDTO;
  status: JobStatus;
  creationDate: string;
  completionDate?: string;
  msg?: string;
  outputId?: string;
  exitCode?: number;
  solverStats?: string;
  owner?: JobUserInfo;
}

export type GetJobsParams =
  | {
      studyId: string;
    }
  | {
      studyId?: never;
      filterOrphans?: boolean;
      latest?: number;
    };
