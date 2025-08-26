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

import type { AxiosResponse } from "axios";
import client from "../../../../../../../../services/api/client";
import type { StudyMetadata } from "../../../../../../../../types/types";
import type { ScenarioConfig, ScenarioType } from "./types";

////////////////////////////////////////////////////////////////
// API Services
////////////////////////////////////////////////////////////////

/**
 * Fetches the scenario configuration for a specific scenario type
 *
 * @param studyId - The study identifier
 * @param scenarioType - The type of scenario to fetch
 * @returns The scenario configuration data
 */
export async function getScenarioConfigByType(
  studyId: StudyMetadata["id"],
  scenarioType: ScenarioType,
): Promise<ScenarioConfig> {
  const res = await client.get<ScenarioConfig>(
    `v1/studies/${studyId}/config/scenariobuilder/${scenarioType}`,
  );
  return res.data;
}

/**
 * Updates the scenario builder configuration for a specific scenario type
 *
 * @param studyId - The study identifier
 * @param data - The configuration data to update
 * @param scenarioType - The type of scenario to update
 * @returns The API response
 */
export function updateScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  data: Partial<ScenarioConfig>,
  scenarioType: ScenarioType,
) {
  return client.put<AxiosResponse<null, string>>(
    `v1/studies/${studyId}/config/scenariobuilder/${scenarioType}`,
    data,
  );
}

/**
 * Fetches all scenario configurations for a study
 * (Not yet implemented in the API, added for future use)
 *
 * @param studyId - The study identifier
 * @returns All scenario configurations
 */
export async function getAllScenarioConfigs(studyId: StudyMetadata["id"]): Promise<ScenarioConfig> {
  const res = await client.get<ScenarioConfig>(`v1/studies/${studyId}/config/scenariobuilder`);
  return res.data;
}
