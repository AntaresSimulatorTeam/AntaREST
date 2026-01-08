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

import type {
  DataProcessor,
  EntityYearlyValues,
  Level1Data,
  Level1Display,
  Level2Data,
  Level2Display,
  Level3Data,
  Level3Display,
  NonNullableScenarioData,
  ScenarioData,
  ScenarioDisplayMap,
} from "./types";

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

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
 * Converts flattened Level 1 representation back to nested Level 3 structure
 *
 * @param flatConfig - Flattened configuration with "entityId - subEntityId" keys
 * @returns Nested entity-subentity structure for the API
 *
 * @example
 * Input:  { "storage1 - constraint1": { "1": 10, "2": 20 } }
 * Output: { "storage1": { "constraint1": { "1": 10, "2": 20 } } }
 */
export function flattenedToNestedStructure(
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

////////////////////////////////////////////////////////////////
// Validation Helpers
////////////////////////////////////////////////////////////////

/**
 * Validates that the composite key has the expected format
 *
 * @param key - The composite key to validate
 * @returns True if valid, false otherwise
 */
function isValidCompositeKey(key: string): boolean {
  if (!key || typeof key !== "string") {
    return false;
  }

  const parts = key.split(" - ");
  return parts.length === 2 && parts[0].trim() !== "" && parts[1].trim() !== "";
}

/**
 * Extracts entity and sub-entity IDs from a composite key
 *
 * @param compositeKey - The composite key
 * @returns Tuple of [entityId, subEntityId]
 */
function parseCompositeKey(compositeKey: string): [string, string] {
  if (!isValidCompositeKey(compositeKey)) {
    throw new Error(
      `Invalid composite key format: "${compositeKey}". Expected format: "entityId - subEntityId"`,
    );
  }

  const [entityId, subEntityId] = compositeKey.split(" - ");
  return [entityId.trim(), subEntityId.trim()];
}

/**
 * Creates a composite key from entity and sub-entity IDs
 *
 * @param entityId - The entity identifier
 * @param subEntityId - The sub-entity identifier
 * @returns Composite key in the format "entityId - subEntityId"
 */
function createCompositeKey(entityId: string, subEntityId: string): string {
  if (!entityId?.trim() || !subEntityId?.trim()) {
    throw new Error(
      `Entity ID and Sub-entity ID must be non-empty strings, entityId: "${entityId}", subEntityId: "${subEntityId}"`,
    );
  }

  return `${entityId.trim()} - ${subEntityId.trim()}`;
}
