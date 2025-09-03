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
  EntityYearlyValues,
  Level1Data,
} from "@/services/api/studies/config/scenarioBuilder/types";

// UI representation for Level 1 data (direct use)
export type Level1Display = Level1Data;

// UI representation for Level 2 data (with area selection)
export interface Level2Display {
  areas: string[];
  entities: Record<string, Record<string, EntityYearlyValues>>;
}

// UI representation for Level 3 data (with area selection)
export interface Level3Display {
  areas: string[];
  // Flattened representation with composite keys: "entityId - subEntityId"
  flattenedEntities: Record<string, Level1Data>;
}

// Any UI-ready configuration type
export type ScenarioDisplay = Level1Display | Level2Display | Level3Display;

// Configuration types that require area selection
export type AreaSelectionDisplay = Level2Display | Level3Display;

export interface ScenarioDisplayMap {
  load: Level1Display;
  thermal: Level2Display;
  hydro: Level1Display;
  wind: Level1Display;
  solar: Level1Display;
  ntc: Level1Display;
  renewable: Level2Display;
  hydroInitialLevels: Level1Display;
  bindingConstraints: Level1Display;
  hydroFinalLevels: Level1Display;
  shortTermStorageInflows: Level2Display;
  shortTermStorageAdditionalConstraints: Level3Display;
}

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
