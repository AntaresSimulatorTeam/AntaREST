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

import { SCENARIOS } from "@/services/api/studies/config/scenarioBuilder/constants";
import {
  isLevel2Scenario,
  isLevel3Scenario,
  type ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

interface ScenarioMetadata {
  level: 1 | 2 | 3;
  requiresAreaSelection: boolean;
  minVersion?: number;
}

const SCENARIO_METADATA: Record<ScenarioType, ScenarioMetadata> = {
  // Level 1 scenarios (area → values)
  load: { level: 1, requiresAreaSelection: false },
  hydro: { level: 1, requiresAreaSelection: false },
  wind: { level: 1, requiresAreaSelection: false },
  solar: { level: 1, requiresAreaSelection: false },
  ntc: { level: 1, requiresAreaSelection: false, minVersion: 820 },
  hydroInitialLevels: { level: 1, requiresAreaSelection: false },
  bindingConstraints: { level: 1, requiresAreaSelection: false, minVersion: 870 },
  hydroFinalLevels: { level: 1, requiresAreaSelection: false, minVersion: 920 },

  // Level 2 scenarios (area → entity → values)
  thermal: { level: 2, requiresAreaSelection: true },
  renewable: { level: 2, requiresAreaSelection: true, minVersion: 810 },
  shortTermStorageInflows: { level: 2, requiresAreaSelection: true, minVersion: 930 },

  // Level 3 scenarios (area → entity → subentity → values)
  shortTermStorageAdditionalConstraints: { level: 3, requiresAreaSelection: true, minVersion: 930 },
};

////////////////////////////////////////////////////////////////
// Function Helpers
////////////////////////////////////////////////////////////////

/**
 * Checks if a scenario requires area selection
 *
 * @param type - The scenario type to check
 * @returns True if the scenario requires area selection, false otherwise
 */
export function requiresAreaSelection(type: ScenarioType): boolean {
  return isLevel2Scenario(type) || isLevel3Scenario(type);
}

/**
 * Get metadata for a scenario type
 *
 * @param type - The scenario type to get metadata for
 * @returns The metadata for the scenario type
 */
export function getScenarioMetadata(type: ScenarioType) {
  return SCENARIO_METADATA[type];
}

/**
 * Check if a scenario is available for the given study version
 *
 * @param type - The scenario type to check
 * @param version - The study version (3-digit format, e.g., 930 for v9.3)
 * @returns True if the scenario is available for this version, false otherwise
 */
export function isScenarioAvailableForVersion(type: ScenarioType, version: number): boolean {
  const metadata = getScenarioMetadata(type);
  return !metadata.minVersion || version >= metadata.minVersion;
}

/**
 * Filter scenarios by study version, only returning those available for the version
 *
 * @param version - The study version (3-digit format)
 * @returns Array of scenario types available for this version
 */
export function getAvailableScenariosForVersion(version: number): ScenarioType[] {
  return SCENARIOS.filter((scenario) => isScenarioAvailableForVersion(scenario, version));
}
