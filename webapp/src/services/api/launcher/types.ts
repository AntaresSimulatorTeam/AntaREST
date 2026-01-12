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

import type { StudyMetadata } from "@/types/types";

export interface XpansionParamsDTO {
  enabled?: boolean;
  output_id?: string;
  sensitivity_mode?: boolean;
  adequacy_criterion?: boolean;
}

interface XpansionParams {
  enabled?: boolean;
  outputId?: string;
  sensitivityMode?: boolean;
  adequacyCriterion?: boolean;
}

export interface LauncherParamsDTO {
  adequacy_patch?: Record<string, string | number | boolean>;
  nb_cpu?: number;
  post_processing?: boolean;
  time_limit?: number;
  xpansion?: XpansionParamsDTO;
  xpansion_r_version?: boolean;
  archive_output?: boolean;
  auto_unzip?: boolean;
  output_suffix?: string;
  other_options?: string;
}

export interface LauncherParams {
  nbCores?: number;
  xpansion?: XpansionParams;
  outputSuffix?: string;
  otherOptions?: string;
  autoUnzip?: boolean;
}

interface RangeWithDefault {
  min: number;
  max: number;
  default: number;
}

export interface LauncherDTO {
  id: string;
  name: string;
  nbCores: RangeWithDefault;
  timeLimit: RangeWithDefault;
  versions: string[];
}

// This type uses semantic versioning (see `adaptLaunchersConfigDtoToLaunchersConfig()` function)
export type Launcher = LauncherDTO;

export interface LaunchersConfigDTO {
  launchers: LauncherDTO[];
  defaultLauncher: string;
}

export interface LaunchersConfig extends LaunchersConfigDTO {
  launchers: Launcher[];
}

////////////////////////////////////////////////////////////////
// Function Types
////////////////////////////////////////////////////////////////

export interface LaunchStudyParams {
  studyId: StudyMetadata["id"];
  launcherId: LauncherDTO["id"];
  version: StudyMetadata["version"];
  solverPresetsId?: string;
  launcherParams?: LauncherParams;
}

export interface GetLauncherVersionsParams {
  launcherId?: LauncherDTO["id"]; // If not specified, retrieve the versions of the default launcher
}

export interface JobCreationDTO {
  job_id: string;
}
