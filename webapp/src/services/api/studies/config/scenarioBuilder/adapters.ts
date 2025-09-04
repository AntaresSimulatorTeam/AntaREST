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
  Level2Data,
  Level3Data,
  NonNullableScenarioData,
  ScenarioData,
  ScenarioType,
} from "./types";
import {
  createCompositeKey,
  isLevel1Scenario,
  isLevel2Scenario,
  isLevel3Scenario,
  parseCompositeKey,
} from "./utils";

export type Level1Display = Level1Data;

export interface Level2Display {
  areas: string[];
  entities: Record<string, Record<string, EntityYearlyValues>>;
}

export interface Level3Display {
  areas: string[];
  // Flattened representation with composite keys: "entityId - subEntityId"
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
// UI to DTO Adapters
////////////////////////////////////////////////////////////////

/**
 * Converts flattened Level 1 representation back to nested Level 3 structure
 *
 * @param flatConfig - Flattened configuration with "entityId - subEntityId" keys
 * @returns Nested entity-subentity structure for the API
 *
 * @example
 * Input:  { "storage1 - constraint1": { "1": 10, "2": 20 } }
 * Output: { "storage1": { "constraint1": { "1": 10, "2": 20 } } }
 */
function flattenedToNestedStructure(
  flatConfig: Level1Data,
): Record<string, Record<string, EntityYearlyValues>> {
  const nestedStructure: Record<string, Record<string, EntityYearlyValues>> = {};

  Object.entries(flatConfig).forEach(([compositeKey, yearlyValues]) => {
    const [entityId, subEntityId] = parseCompositeKey(compositeKey);

    if (!nestedStructure[entityId]) {
      nestedStructure[entityId] = {};
    }

    nestedStructure[entityId][subEntityId] = yearlyValues;
  });

  return nestedStructure;
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
export function adaptScenarioFormToDto(
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

////////////////////////////////////////////////////////////////
// DTO to UI Adapters
////////////////////////////////////////////////////////////////

/**
 * Converts nested entity-subentity structure to flattened representation
 *
 * @param nestedStructure - Nested configuration from the API
 * @returns Flattened configuration with composite keys
 *
 * @example
 * Input:  { "storage1": { "constraint1": { "1": 10, "2": 20 } } }
 * Output: { "storage1 - constraint1": { "1": 10, "2": 20 } }
 */
export function nestedStructureToFlattened(
  nestedStructure: Record<string, Record<string, EntityYearlyValues>>,
): Level1Data {
  const flattenedData: Level1Data = {};

  Object.entries(nestedStructure).forEach(([entityId, subEntities]) => {
    Object.entries(subEntities).forEach(([subEntityId, yearlyValues]) => {
      const compositeKey = createCompositeKey(entityId, subEntityId);
      flattenedData[compositeKey] = yearlyValues;
    });
  });

  return flattenedData;
}

/**
 * Converts API data to UI representation based on scenario type
 * Primarily transforms Level 3 scenarios to flattened representation
 *
 * @param scenarioType - Type of scenario being processed
 * @param dto - Data from the API
 * @param areaId - Selected area ID (for Level 2 and 3 scenarios)
 * @returns UI-ready data structure
 */
export function adaptScenarioDtoToForm<T extends ScenarioType>(
  scenarioType: T,
  dto: ScenarioData,
  areaId?: string,
): Level1Data {
  const scenarioData = dto[scenarioType];

  if (!scenarioData) {
    return {};
  }

  // For Level 1 scenarios, return directly
  if (isLevel1Scenario(scenarioType)) {
    return scenarioData as Level1Data;
  }

  // For Level 2 scenarios with area selection, return area data
  if (isLevel2Scenario(scenarioType) && areaId) {
    const areaData = (scenarioData as Level2Data)[areaId];
    return areaData || {};
  }

  // For Level 3 scenarios with area selection, flatten the structure
  if (isLevel3Scenario(scenarioType) && areaId) {
    const areaData = (scenarioData as Level3Data)[areaId];
    return areaData ? nestedStructureToFlattened(areaData) : {};
  }

  return {};
}

////////////////////////////////////////////////////////////////
// Display Transformations
////////////////////////////////////////////////////////////////

type DataProcessor<T, U = T> = (data: T) => U;

const processors: {
  [K in keyof NonNullableScenarioData]: DataProcessor<
    NonNullableScenarioData[K],
    ScenarioDisplayMap[K]
  >;
} = {
  load: processLevel1Data,
  thermal: processLevel2Data,
  hydro: processLevel1Data,
  wind: processLevel1Data,
  solar: processLevel1Data,
  ntc: processLevel1Data,
  renewable: processLevel2Data,
  hydroInitialLevels: processLevel1Data,
  bindingConstraints: processLevel1Data,
  hydroFinalLevels: processLevel1Data,
  shortTermStorageInflows: processLevel2Data,
  shortTermStorageAdditionalConstraints: processLevel3Data,
};

/**
 * Processes Level 1 data (direct area to yearly values)
 *
 * @param data - The Level 1 data from API
 * @returns The processed Level 1 display data
 */
function processLevel1Data(data: Level1Data): Level1Display {
  return Object.entries(data).reduce<Level1Data>((acc, [areaId, yearlyValue]) => {
    acc[areaId] = yearlyValue;
    return acc;
  }, {});
}

/**
 * Processes Level 2 data (area → entity → yearly values)
 * Extracts areas and organizes entities by area
 *
 * @param data - The Level 2 data from API
 * @returns Object with areas list and entity configurations
 */
function processLevel2Data(data: Level2Data): Level2Display {
  return Object.entries(data).reduce<Level2Display>(
    (acc, [areaId, entityConfig]) => {
      acc.areas.push(areaId);
      acc.entities[areaId] = entityConfig;
      return acc;
    },
    { areas: [], entities: {} },
  );
}

/**
 * Processes Level 3 data (area → entity → subentity → yearly values)
 * Extracts areas and flattens the nested structure for UI display
 *
 * @param data - The Level 3 data from API
 * @returns Object with areas list and flattened entity configurations
 */
function processLevel3Data(data: Level3Data): Level3Display {
  return Object.entries(data).reduce<Level3Display>(
    (acc, [areaId, entityConfig]) => {
      acc.areas.push(areaId);
      // Flatten the nested structure for UI display
      acc.flattenedEntities[areaId] = nestedStructureToFlattened(entityConfig);
      return acc;
    },
    { areas: [], flattenedEntities: {} },
  );
}

/**
 * Retrieves and processes the configuration for a specific scenario type
 *
 * @param data - Full scenario data from API
 * @param scenario - The specific scenario type to process
 * @returns The processed display data or undefined if not found
 */
export function getConfigByScenario<K extends keyof ScenarioData>(
  data: ScenarioData,
  scenario: K,
): ScenarioDisplayMap[K] | undefined {
  const scenarioData = data[scenario];

  if (!scenarioData) {
    return undefined;
  }

  return processors[scenario](scenarioData);
}
