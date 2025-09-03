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
  LEVEL1_SCENARIOS,
  LEVEL2_SCENARIOS,
  LEVEL3_SCENARIOS,
  SCENARIO_METADATA,
  SCENARIOS,
} from "./constants";
import type {
  Level1ScenarioType,
  Level2ScenarioType,
  Level3ScenarioType,
  ScenarioType,
} from "./types";

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
  if (!key || typeof key !== "string") {
    return false;
  }

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
    throw new Error(
      `Invalid composite key format: "${compositeKey}". Expected format: "entityId - subEntityId"`,
    );
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
 * @throws {Error} If either ID is empty or invalid
 */
export function createCompositeKey(storageId: string, constraintId: string): string {
  if (!storageId || typeof storageId !== "string" || storageId.trim() === "") {
    throw new Error(`Storage ID must be a non-empty string, got: "${storageId}"`);
  }

  if (!constraintId || typeof constraintId !== "string" || constraintId.trim() === "") {
    throw new Error(`Constraint ID must be a non-empty string, got: "${constraintId}"`);
  }

  return `${storageId.trim()} - ${constraintId.trim()}`;
}

////////////////////////////////////////////////////////////////
// Version Management
////////////////////////////////////////////////////////////////

/**
 * Check if a scenario is available for the given study version
 *
 * @param type - The scenario type to check
 * @param studyVersion - The study version (3-digit format, e.g., 930 for v9.3)
 * @returns True if the scenario is available for this version, false otherwise
 */
export function isScenarioAvailableForVersion(type: ScenarioType, studyVersion: number): boolean {
  const metadata = getScenarioMetadata(type);
  return !metadata.minVersion || studyVersion >= metadata.minVersion;
}

/**
 * Filter scenarios by study version, only returning those available for the version
 *
 * @param studyVersion - The study version (3-digit format)
 * @returns Array of scenario types available for this version
 */
export function getAvailableScenariosForVersion(studyVersion: number): ScenarioType[] {
  return SCENARIOS.filter((scenario) => isScenarioAvailableForVersion(scenario, studyVersion));
}
