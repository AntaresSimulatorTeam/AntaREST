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

import type { StudyMetadata } from "@/types/types";
import type { Launcher } from "../study";

export interface XpansionParamsDTO {
  enabled?: boolean;
  sensitivity_mode?: boolean;
  output_id?: string;
  adequacy_criterion?: boolean;
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

interface XpansionConfig {
  enabled?: boolean;
  adequacyCriterion?: boolean;
  sensitivityMode?: boolean;
  outputId?: string;
}

export interface LauncherConfig {
  outputSuffix?: string;
  otherOptions?: string;
  autoUnzip?: boolean;
  xpansion?: XpansionConfig;
  nbCores?: number;
}

export interface LaunchStudyParams {
  studyId: StudyMetadata["id"];
  launcherId: Launcher["id"];
  version: StudyMetadata["version"];
  config?: LauncherConfig;
}

export interface LaunchStudyParams {
  studyId: StudyMetadata["id"];
  launcherId: Launcher["id"];
  version: StudyMetadata["version"];
  config?: LauncherConfig;
}

export interface JobCreationDTO {
  job_id: string;
}
