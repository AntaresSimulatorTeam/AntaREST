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

import {
  isLevel1Scenario,
  isLevel2Scenario,
  isLevel3Scenario,
  type Level1Data,
  type ScenarioData,
  type ScenarioType,
} from "./types";
import { flattenedToNestedStructure, getConfigByScenario } from "./utils";

/**
 * Converts API data to form data for UI editing
 * Now includes the logic from getConfigByScenario for seamless integration
 *
 * @param scenarioType - Type of scenario being processed
 * @param dto - Data from the API
 * @returns Display data structure (same as getConfigByScenario)
 */
export function adaptScenarioBuilderDtoToForm<T extends ScenarioType>(
  scenarioType: T,
  dto: ScenarioData,
) {
  const scenarioData = dto[scenarioType];

  if (!scenarioData) {
    return {};
  }

  return getConfigByScenario(dto, scenarioType);
}

/**
 * Converts UI form data to API data structure based on scenario type
 *
 * @param scenarioType - Type of scenario being processed
 * @param formData - Form data from the UI
 * @param areaId - Selected area ID (required for Level 2 and 3 scenarios)
 * @returns Properly formatted data for the API
 *
 * @throws {Error} If area ID is required but not provided
 */
export function adaptScenarioBuilderFormToDto(
  scenarioType: ScenarioType,
  formData: Level1Data,
  areaId?: string,
): Partial<ScenarioData> {
  // Level 1 scenarios: direct mapping
  if (isLevel1Scenario(scenarioType)) {
    return { [scenarioType]: formData };
  }

  // Level 2 and 3 scenarios require area ID
  if (!areaId) {
    throw new Error(`Area ID is required for ${scenarioType} scenario`);
  }

  // Level 3 scenarios: transform flattened structure to nested
  if (isLevel3Scenario(scenarioType)) {
    const nestedStructure = flattenedToNestedStructure(formData);
    return { [scenarioType]: { [areaId]: nestedStructure } };
  }

  // Level 2 scenarios: wrap in area structure
  if (isLevel2Scenario(scenarioType)) {
    return { [scenarioType]: { [areaId]: formData } };
  }

  // Should never reach here
  throw new Error(`Unknown scenario type: ${scenarioType}`);
}
