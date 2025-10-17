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

import client from "../client";
import type { JobCreationDTO, LauncherParamsDTO, LaunchStudyParams } from "./types";

const BASE_URL = "/v1/launcher";

export async function launchStudy({ studyId, launcherId, version, config }: LaunchStudyParams) {
  const launcherParams: LauncherParamsDTO = {
    nb_cpu: config?.nbCores,
    xpansion: config?.xpansion && {
      enabled: config.xpansion?.enabled,
      adequacy_criterion: config.xpansion?.adequacyCriterion,
      sensitivity_mode: config.xpansion?.sensitivityMode,
      output_id: config.xpansion?.outputId,
    },
    auto_unzip: config?.autoUnzip,
    output_suffix: config?.outputSuffix,
    other_options: config?.otherOptions,
  };

  const { data } = await client.post<JobCreationDTO>(`${BASE_URL}/run/${studyId}`, launcherParams, {
    params: { version, launcher: launcherId },
  });

  return data;
}
