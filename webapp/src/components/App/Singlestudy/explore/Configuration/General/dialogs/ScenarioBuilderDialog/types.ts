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

import type {
  Level2Display,
  Level3Display,
  ScenarioDisplayMap,
} from "@/services/api/studies/config/scenarioBuilder/adapters";

// Configuration types that require area selection
export type AreaSelectionDisplay = Level2Display | Level3Display;

////////////////////////////////////////////////////////////////
// Type Guards
////////////////////////////////////////////////////////////////

/**
 * Checks if a configuration has area selection structure
 *
 * @param config - The configuration to check
 * @returns True if the configuration has area selection structure, false otherwise
 */
export function hasAreaSelection(
  config: ScenarioDisplayMap[keyof ScenarioDisplayMap],
): config is AreaSelectionDisplay {
  return (
    config !== undefined &&
    "areas" in config &&
    Array.isArray(config.areas) &&
    config.areas.every((area) => typeof area === "string")
  );
}

/**
 * Checks if a configuration is for Level 2 scenarios
 *
 * @param config - The configuration to check
 * @returns True if the configuration is for Level 2 scenarios, false otherwise
 */
export function isLevel2Display(config: AreaSelectionDisplay): config is Level2Display {
  return "entities" in config;
}

/**
 * Checks if a configuration is for Level 3 scenarios
 *
 * @param config - The configuration to check
 * @returns True if the configuration is for Level 3 scenarios, false otherwise
 */
export function isLevel3Display(config: AreaSelectionDisplay): config is Level3Display {
  return "flattenedEntities" in config;
}
