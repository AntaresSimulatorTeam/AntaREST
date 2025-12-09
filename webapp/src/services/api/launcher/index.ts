/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { compactSemanticVersion } from "@/utils/versionUtils";
import client from "../client";
import { adaptLauncherParamsToDto, adaptLaunchersConfigDtoToLaunchersConfig } from "./adapters";
import type {
  GetLauncherVersionsParams,
  JobCreationDTO,
  LaunchersConfigDTO,
  LaunchStudyParams,
} from "./types";

const BASE_URL = "/v1/launcher";

export async function launchStudy({
  studyId,
  launcherId,
  solverPresetsId,
  version,
  launcherParams,
}: LaunchStudyParams) {
  const { data } = await client.post<JobCreationDTO>(
    `${BASE_URL}/run/${studyId}`,
    launcherParams ? adaptLauncherParamsToDto(launcherParams) : {},
    {
      params: {
        version: compactSemanticVersion(version),
        launcher: launcherId,
        solver_presets_id: solverPresetsId,
      },
    },
  );

  return data;
}

export async function getLauncherVersions({ launcherId }: GetLauncherVersionsParams = {}) {
  const { data } = await client.get<string[]>(`${BASE_URL}/versions`, {
    params: { launcher_id: launcherId },
  });

  return data;
}

export async function getLaunchersConfig() {
  const res = await client.get<LaunchersConfigDTO>("/v1/launcher/launchers");
  return adaptLaunchersConfigDtoToLaunchersConfig(res.data);
}
