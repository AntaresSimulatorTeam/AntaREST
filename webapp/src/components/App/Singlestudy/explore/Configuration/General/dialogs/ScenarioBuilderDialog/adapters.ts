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

import {
  type EntityYearlyValues,
  isLevel1Scenario,
  isLevel2Scenario,
  isLevel3Scenario,
  type Level1Data,
  type Level3Data,
  type ScenarioData,
  type ScenarioDataStructure,
  type ScenarioType,
} from "./types";

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
    const [entityId, subEntityId] = compositeKey.split(" - ");

    if (!entityId || !subEntityId) {
      throw new Error(
        `Invalid composite key format: ${compositeKey}. Expected format: "entityId - subEntityId"`,
      );
    }

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
      const compositeKey = `${entityId} - ${subEntityId}`;
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
 * @param apiData - Data from the API
 * @param areaId - Selected area ID (for Level 2 and 3 scenarios)
 * @returns UI-ready data structure
 */
export function adaptScenarioDtoToForm<T extends ScenarioType>(
  scenarioType: T,
  apiData: ScenarioDataStructure<T>,
  areaId?: string,
): Level1Data {
  // For Level 3 scenarios with area selection, flatten the structure
  if (isLevel3Scenario(scenarioType) && areaId && apiData) {
    const areaData = (apiData as Level3Data)[areaId];

    if (areaData) {
      return nestedStructureToFlattened(areaData);
    }
  }

  // For other scenarios, return as-is
  return (apiData as Level1Data) || {};
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
export function isValidCompositeKey(key: string): boolean {
  const parts = key.split(" - ");
  return parts.length === 2 && parts[0].trim() !== "" && parts[1].trim() !== "";
}

/**
 * Extracts storage and constraint IDs from a composite key
 *
 * @param compositeKey - The composite key
 * @returns Tuple of [storageId, constraintId]
 * @throws {Error} If the key format is invalid
 */
export function parseCompositeKey(compositeKey: string): [string, string] {
  if (!isValidCompositeKey(compositeKey)) {
    throw new Error(`Invalid composite key format: ${compositeKey}`);
  }

  const [storageId, constraintId] = compositeKey.split(" - ");
  return [storageId.trim(), constraintId.trim()];
}

/**
 * Creates a composite key from storage and constraint IDs
 *
 * @param storageId - The storage identifier
 * @param constraintId - The constraint identifier
 * @returns Composite key in the format "storageId - constraintId"
 */
export function createCompositeKey(storageId: string, constraintId: string): string {
  return `${storageId} - ${constraintId}`;
}
