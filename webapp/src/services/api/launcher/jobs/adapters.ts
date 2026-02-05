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
import type { Job, JobDTO } from "./types";

export function adaptJobDtoToJob(dto: JobDTO): Job {
  return {
    id: dto.id,
    studyId: dto.study_id,
    launcher: dto.launcher,
    launcherParams:
      typeof dto.launcher_params === "string"
        ? (JSON.parse(dto.launcher_params) as LauncherParamsDTO)
        : undefined,
    status: dto.status,
    creationDate: dto.creation_date,
    completionDate: dto.completion_date,
    msg: dto.msg,
    outputId: dto.output_id,
    exitCode: dto.exit_code,
    solverStats: dto.solver_stats,
    owner: dto.owner,
  };
}
