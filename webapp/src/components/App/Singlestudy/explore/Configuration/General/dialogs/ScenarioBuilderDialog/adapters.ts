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
  type ScenarioType,
  type ScenarioConfig,
  type GenericScenarioConfig,
  type StorageConstraintsConfig,
  isSimpleScenario,
  isClusterScenario,
  isConstraintScenario,
} from "./types";

////////////////////////////////////////////////////////////////
// UI to DTO Adapters
////////////////////////////////////////////////////////////////

/**
 * Adapts the flattened UI representation of storage constraints back to the nested DTO structure
 *
 * @param flatConfig - Flattened configuration with "storageId - constraintId" keys
 * @returns Nested configuration for the API
 *
 * @example
 * Input:  { "storage1 - constraint1": { "1": 10, "2": 20 } }
 * Output: { "storage1": { "constraint1": { "1": 10, "2": 20 } } }
 */
function adaptFlattenedConstraintsToDto(
  flatConfig: GenericScenarioConfig,
): StorageConstraintsConfig {
  const nestedStructure: StorageConstraintsConfig = {};

  Object.entries(flatConfig).forEach(([compositeKey, yearlyValues]) => {
    const [storageId, constraintId] = compositeKey.split(" - ");

    if (!storageId || !constraintId) {
      throw new Error(
        `Invalid composite key format: ${compositeKey}. Expected format: "storageId - constraintId"`,
      );
    }

    if (!nestedStructure[storageId]) {
      nestedStructure[storageId] = {};
    }

    nestedStructure[storageId][constraintId] = yearlyValues;
  });

  return nestedStructure;
}

/**
 * Adapts UI form data to the API DTO format based on the scenario type
 *
 * @param scenarioType - The type of scenario being processed
 * @param formData - The form data from the UI
 * @param areaId - The selected area ID (required for cluster and constraint scenarios)
 * @returns Properly formatted DTO for the API
 *
 * @throws {Error} If area ID is required but not provided
 */
export function adaptScenarioFormToDto(
  scenarioType: ScenarioType,
  formData: Record<string, any>,
  areaId?: string,
): Partial<ScenarioConfig> {
  // Simple scenarios: direct mapping
  if (isSimpleScenario(scenarioType)) {
    return { [scenarioType]: formData };
  }

  // Complex scenarios require area ID
  if (!areaId) {
    throw new Error(`Area ID is required for ${scenarioType} scenario`);
  }

  // Constraint scenarios: transform flattened structure to nested
  if (isConstraintScenario(scenarioType)) {
    const nestedConstraints = adaptFlattenedConstraintsToDto(formData);
    return { [scenarioType]: { [areaId]: nestedConstraints } };
  }

  // Cluster scenarios: wrap in area structure
  if (isClusterScenario(scenarioType)) {
    return { [scenarioType]: { [areaId]: formData } };
  }

  // Should never reach here with proper types
  throw new Error(`Unknown scenario type: ${scenarioType}`);
}

////////////////////////////////////////////////////////////////
// DTO to UI Adapters
////////////////////////////////////////////////////////////////

/**
 * Adapts nested storage constraints from DTO to flattened UI representation
 *
 * @param nestedConfig - Nested configuration from the API
 * @returns Flattened configuration for the UI with composite keys
 *
 * @example
 * Input:  { "storage1": { "constraint1": { "1": 10, "2": 20 } } }
 * Output: { "storage1 - constraint1": { "1": 10, "2": 20 } }
 */
export function adaptConstraintsDtoToFlattened(
  nestedConfig: StorageConstraintsConfig,
): GenericScenarioConfig {
  const flattenedConfig: GenericScenarioConfig = {};

  Object.entries(nestedConfig).forEach(([storageId, constraints]) => {
    Object.entries(constraints).forEach(([constraintId, yearlyValues]) => {
      const compositeKey = `${storageId} - ${constraintId}`;
      flattenedConfig[compositeKey] = yearlyValues;
    });
  });

  return flattenedConfig;
}

/**
 * Adapts API DTO to UI representation based on the scenario type
 * This is primarily used for transforming constraint scenarios
 *
 * @param scenarioType - The type of scenario being processed
 * @param dtoData - The data from the API
 * @param areaId - The selected area ID (for constraint scenarios)
 * @returns UI-ready data structure
 */
export function adaptScenarioDtoToForm(
  scenarioType: ScenarioType,
  dtoData: any,
  areaId?: string,
): GenericScenarioConfig {
  // For constraint scenarios with area selection, flatten the structure
  if (isConstraintScenario(scenarioType) && areaId && dtoData) {
    const areaData = dtoData[areaId];
    if (areaData) {
      return adaptConstraintsDtoToFlattened(areaData);
    }
  }

  // For other scenarios, return as-is
  return dtoData || {};
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
