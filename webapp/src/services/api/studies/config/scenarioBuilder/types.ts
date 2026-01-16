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
import { LEVEL1_SCENARIOS, LEVEL2_SCENARIOS, LEVEL3_SCENARIOS, type SCENARIOS } from "./constants";

////////////////////////////////////////////////////////////////
// Core Types
////////////////////////////////////////////////////////////////

export type ScenarioType = (typeof SCENARIOS)[number];
export type Level1ScenarioType = (typeof LEVEL1_SCENARIOS)[number];
export type Level2ScenarioType = (typeof LEVEL2_SCENARIOS)[number];
export type Level3ScenarioType = (typeof LEVEL3_SCENARIOS)[number];
export type DataProcessor<T, U = T> = (data: T) => U;

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

// Maps scenario type to its appropriate data structure
export type ScenarioDataStructure<T extends ScenarioType> = T extends Level1ScenarioType
  ? Level1Data
  : T extends Level2ScenarioType
    ? Level2Data
    : T extends Level3ScenarioType
      ? Level3Data
      : never;

////////////////////////////////////////////////////////////////
// Display Types
////////////////////////////////////////////////////////////////

export type Level1Display = Level1Data;

export interface Level2Display {
  areas: string[];
  entities: Record<string, Record<string, EntityYearlyValues>>;
}

export interface Level3Display {
  areas: string[];
  flattenedEntities: Record<string, Level1Data>;
}

export type ScenarioDisplay = Level1Display | Level2Display | Level3Display;

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
// API Types
////////////////////////////////////////////////////////////////

export interface BaseScenarioBuilderParams {
  studyId: StudyMetadata["id"];
}

export interface GetScenarioBuilderParams extends BaseScenarioBuilderParams {
  scenarioType: ScenarioType;
}

export interface UpdateScenarioBuilderParams extends BaseScenarioBuilderParams {
  scenarioType: ScenarioType;
  values: Partial<ScenarioData>;
}

export interface UpdateScenarioBuilderFormParams extends UpdateScenarioBuilderParams {
  values: Level1Data;
  areaId?: string;
}

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
  return LEVEL1_SCENARIOS.includes(type);
}

/**
 * Checks if a scenario has Level 2 structure (area → entity → values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario has Level 2 structure, false otherwise
 */
export function isLevel2Scenario(type: ScenarioType): type is Level2ScenarioType {
  return LEVEL2_SCENARIOS.includes(type);
}

/**
 * Checks if a scenario has Level 3 structure (area → entity → subentity → values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario has Level 3 structure, false otherwise
 */
export function isLevel3Scenario(type: ScenarioType): type is Level3ScenarioType {
  return LEVEL3_SCENARIOS.includes(type);
}
