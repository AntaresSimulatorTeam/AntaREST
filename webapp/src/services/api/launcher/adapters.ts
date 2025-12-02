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

import { toSemanticVersion } from "@/utils/versionUtils";
import type {
  LauncherParams,
  LauncherParamsDTO,
  LaunchersConfig,
  LaunchersConfigDTO,
} from "./types";

export function adaptLauncherParamsToDto(params: LauncherParams): LauncherParamsDTO {
  return {
    nb_cpu: params.nbCores,
    xpansion: params.xpansion && {
      enabled: params.xpansion.enabled,
      adequacy_criterion: params.xpansion.adequacyCriterion,
      sensitivity_mode: params.xpansion.sensitivityMode,
      output_id: params.xpansion.outputId,
    },
    auto_unzip: params.autoUnzip,
    output_suffix: params.outputSuffix,
    other_options: params.otherOptions,
  };
}

export function adaptLaunchersConfigDtoToLaunchersConfig(dto: LaunchersConfigDTO): LaunchersConfig {
  return {
    ...dto,
    launchers: dto.launchers.map((launcher) => ({
      ...launcher,
      // The API don't follow semantic versioning format, minor and patch components may be missing
      versions: launcher.versions.map(toSemanticVersion),
    })),
  };
}
