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

/**
 * All available scenario types in the application
 */

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SCENARIOS = [
  "load",
  "thermal",
  "hydro",
  "wind",
  "solar",
  "ntc",
  "renewable",
  "hydroInitialLevels",
  "bindingConstraints",
  "hydroFinalLevels", // Since v9.2
  "shortTermStorageInflows", // Since v9.3
  "shortTermStorageAdditionalConstraints", // Since v9.3
] as const;

// Scenarios with structure: area → yearly values
export const LEVEL1_SCENARIOS = [
  "load",
  "hydro",
  "wind",
  "solar",
  "ntc",
  "hydroInitialLevels",
  "bindingConstraints",
  "hydroFinalLevels",
] as const;

// Scenarios with structure: area → entity → yearly values
export const LEVEL2_SCENARIOS = ["thermal", "renewable", "shortTermStorageInflows"] as const;

// Scenarios with structure: area → entity → subentity → yearly values
export const LEVEL3_SCENARIOS = ["shortTermStorageAdditionalConstraints"] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ScenarioType = (typeof SCENARIOS)[number];
export type Level1ScenarioType = (typeof LEVEL1_SCENARIOS)[number];
export type Level2ScenarioType = (typeof LEVEL2_SCENARIOS)[number];
export type Level3ScenarioType = (typeof LEVEL3_SCENARIOS)[number];

/**
 * Yearly configuration values, either a number or uninitialized ("rand")
 *
 * @example { "0": 120, "1": "", "2": 150 }
 */
export type YearlyValues = number | "";

/**
 * Maps entity identifiers to their yearly values
 *
 * @example { "Area1": { "0": 10, "1": 20, "2": "" } }
 */
export type EntityYearlyValues = Record<string, YearlyValues>;

/**
 * Level 1: Area → Yearly Values
 *
 * @example { "Area1": { "0": 10, "1": 20 }, "Area2": { "0": 30, "1": 40 } }
 */
export type Level1Data = Record<string, EntityYearlyValues>;

/**
 * Level 2: Area → Entity → Yearly Values
 *
 * @example { "Area1": { "Entity1": { "0": 10 }, "Entity2": { "1": 20 } } }
 */
export type Level2Data = Record<string, Record<string, EntityYearlyValues>>;

/**
 * Level 3: Area → Entity → SubEntity → Yearly Values
 *
 * @example { "Area1": { "Entity1": { "SubEntity1": { "0": 10 } } } }
 */
export type Level3Data = Record<string, Record<string, Record<string, EntityYearlyValues>>>;

////////////////////////////////////////////////////////////////
// UI Display Types
////////////////////////////////////////////////////////////////

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

////////////////////////////////////////////////////////////////
// API Data Transfer Types
////////////////////////////////////////////////////////////////

export interface ScenarioData {
  load?: Level1Data;
  thermal?: Level2Data;
  hydro?: Level1Data;
  wind?: Level1Data;
  solar?: Level1Data;
  ntc?: Level1Data;
  renewable?: Level2Data;
  hydroInitialLevels?: Level1Data;
  bindingConstraints?: Level1Data;
  hydroFinalLevels?: Level1Data;
  shortTermStorageInflows?: Level2Data;
  shortTermStorageAdditionalConstraints?: Level3Data;
}

export type NonNullableScenarioData = {
  [K in keyof ScenarioData]-?: NonNullable<ScenarioData[K]>;
};

/**
 * Mapping of scenario types to their processed display formats
 */
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
// Type Mapping Helpers
////////////////////////////////////////////////////////////////

// Maps scenario type to its appropriate data structure
export type ScenarioDataStructure<T extends ScenarioType> = T extends Level1ScenarioType
  ? Level1Data
  : T extends Level2ScenarioType
    ? Level2Data
    : T extends Level3ScenarioType
      ? Level3Data
      : never;

// Maps scenario type to its appropriate display structure
export type ScenarioDisplayStructure<T extends ScenarioType> = T extends Level1ScenarioType
  ? Level1Display
  : T extends Level2ScenarioType
    ? Level2Display
    : T extends Level3ScenarioType
      ? Level3Display
      : never;

// Configuration types that require area selection
export type AreaSelectionDisplay = Level2Display | Level3Display;

////////////////////////////////////////////////////////////////
// Type Guards
////////////////////////////////////////////////////////////////

/**
 * Checks if a scenario has Level 1 structure (area → values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario has Level 1 structure, false otherwise
 */
export function isLevel1Scenario(type: ScenarioType): type is Level1ScenarioType {
  return LEVEL1_SCENARIOS.includes(type as Level1ScenarioType);
}

/**
 * Checks if a scenario has Level 2 structure (area → entity → values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario has Level 2 structure, false otherwise
 */
export function isLevel2Scenario(type: ScenarioType): type is Level2ScenarioType {
  return LEVEL2_SCENARIOS.includes(type as Level2ScenarioType);
}

/**
 * Checks if a scenario has Level 3 structure (area → entity → subentity → values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario has Level 3 structure, false otherwise
 */
export function isLevel3Scenario(type: ScenarioType): type is Level3ScenarioType {
  return LEVEL3_SCENARIOS.includes(type as Level3ScenarioType);
}

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

////////////////////////////////////////////////////////////////
// Scenario Metadata
////////////////////////////////////////////////////////////////

interface ScenarioMetadata {
  level: 1 | 2 | 3;
  requiresAreaSelection: boolean;
}

export const SCENARIO_METADATA: Record<ScenarioType, ScenarioMetadata> = {
  // Level 1 scenarios (area → values)
  load: { level: 1, requiresAreaSelection: false },
  hydro: { level: 1, requiresAreaSelection: false },
  wind: { level: 1, requiresAreaSelection: false },
  solar: { level: 1, requiresAreaSelection: false },
  ntc: { level: 1, requiresAreaSelection: false },
  hydroInitialLevels: { level: 1, requiresAreaSelection: false },
  bindingConstraints: { level: 1, requiresAreaSelection: false },
  hydroFinalLevels: { level: 1, requiresAreaSelection: false },

  // Level 2 scenarios (area → entity → values)
  thermal: { level: 2, requiresAreaSelection: true },
  renewable: { level: 2, requiresAreaSelection: true },
  shortTermStorageInflows: { level: 2, requiresAreaSelection: true },

  // Level 3 scenarios (area → entity → subentity → values)
  shortTermStorageAdditionalConstraints: { level: 3, requiresAreaSelection: true },
};

/**
 * Get metadata for a scenario type
 *
 * @param type - The scenario type to get metadata for
 * @returns The metadata for the scenario type
 */
export function getScenarioMetadata(type: ScenarioType): ScenarioMetadata {
  return SCENARIO_METADATA[type];
}
