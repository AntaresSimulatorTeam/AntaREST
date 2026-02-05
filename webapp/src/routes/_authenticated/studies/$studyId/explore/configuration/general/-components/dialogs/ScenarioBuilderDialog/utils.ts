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

import { SCENARIOS } from "@/services/api/studies/config/scenarioBuilder/constants";
import {
  isLevel2Scenario,
  isLevel3Scenario,
  type ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";
import semver from "semver";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

interface ScenarioMetadata {
  level: 1 | 2 | 3;
  requiresAreaSelection: boolean;
  minVersion?: string;
}

const SCENARIO_METADATA: Record<ScenarioType, ScenarioMetadata> = {
  // Level 1 scenarios (area → values)
  load: { level: 1, requiresAreaSelection: false },
  hydro: { level: 1, requiresAreaSelection: false },
  wind: { level: 1, requiresAreaSelection: false },
  solar: { level: 1, requiresAreaSelection: false },
  ntc: { level: 1, requiresAreaSelection: false, minVersion: "8.2.0" },
  hydroInitialLevels: { level: 1, requiresAreaSelection: false },
  bindingConstraints: { level: 1, requiresAreaSelection: false, minVersion: "8.7.0" },
  hydroFinalLevels: { level: 1, requiresAreaSelection: false, minVersion: "9.2.0" },

  // Level 2 scenarios (area → entity → values)
  thermal: { level: 2, requiresAreaSelection: true },
  renewable: { level: 2, requiresAreaSelection: true, minVersion: "8.1.0" },
  shortTermStorageInflows: { level: 2, requiresAreaSelection: true, minVersion: "9.3.0" },

  // Level 3 scenarios (area → entity → subentity → values)
  shortTermStorageAdditionalConstraints: {
    level: 3,
    requiresAreaSelection: true,
    minVersion: "9.3.0",
  },
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
 * @param version - The study version
 * @returns True if the scenario is available for this version, false otherwise
 */
export function isScenarioAvailableForVersion(type: ScenarioType, version: string): boolean {
  const metadata = getScenarioMetadata(type);
  return !metadata.minVersion || semver.gte(version, metadata.minVersion);
}

/**
 * Filter scenarios by study version, only returning those available for the version
 *
 * @param version - The study version
 * @returns Array of scenario types available for this version
 */
export function getAvailableScenariosForVersion(version: string): ScenarioType[] {
  return SCENARIOS.filter((scenario) => isScenarioAvailableForVersion(scenario, version));
}
