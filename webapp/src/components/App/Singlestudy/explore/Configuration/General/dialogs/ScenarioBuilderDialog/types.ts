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

////////////////////////////////////////////////////////////////
// Scenario Type Definitions
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

export type ScenarioType = (typeof SCENARIOS)[number];

////////////////////////////////////////////////////////////////
// Scenario Type Categories
////////////////////////////////////////////////////////////////

// Scenarios that have a simple area -> values structure
export const SIMPLE_SCENARIOS = [
  "load",
  "hydro",
  "wind",
  "solar",
  "ntc",
  "hydroInitialLevels",
  "bindingConstraints",
  "hydroFinalLevels",
] as const;

// Scenarios that have area -> cluster/storage -> values structure
export const CLUSTER_SCENARIOS = ["thermal", "renewable", "shortTermStorageInflows"] as const;

// Scenarios that have area -> storage -> constraint -> values structure
export const CONSTRAINT_SCENARIOS = ["shortTermStorageAdditionalConstraints"] as const;

export type SimpleScenarioType = (typeof SIMPLE_SCENARIOS)[number];
export type ClusterScenarioType = (typeof CLUSTER_SCENARIOS)[number];
export type ConstraintScenarioType = (typeof CONSTRAINT_SCENARIOS)[number];

////////////////////////////////////////////////////////////////
// Base Types
////////////////////////////////////////////////////////////////

/**
 * Represents yearly configuration values, which can be either a numerical value or an uninitialized (rand) value represented as an empty string.
 *
 * @example
 * { "0": 120, "1": "", "2": 150 }
 */
export type YearlyValues = number | "";

/**
 * Maps area identifiers to their configuration, each configuration being a series of values or uninitialized (rand) values.
 *
 * @example
 * { "Area1": { "0": 10, "1": 20, "2": 15, "3": "", "4": 50 } }
 */
export type AreaConfig = Record<string, YearlyValues>;

/**
 * Maps cluster identifiers to their configurations within an area, similar to AreaConfig but used at the cluster level.
 *
 * @example
 * { "Cluster1": { "0": 5, "1": "", "2": 20, "3": 30, "4": "" } }
 */
export type ClusterConfig = Record<string, YearlyValues>;

/**
 * Maps storage identifiers to their configurations within an area, similar to AreaConfig but used at the storage level.
 *
 * @example
 * { "Storage1": { "0": 5, "1": "", "2": 20, "3": 30, "4": "" } }
 */
export type StorageConfig = Record<string, YearlyValues>;

/**
 * Configuration for constraints within a storage.
 * Maps constraint identifiers to their yearly values.
 *
 * @example
 * {
 *   "test3": { "1": 10, "2": "", "3": 30 },
 *   "discharge-limit": { "1": 5, "2": 25, "3": "" }
 * }
 */
export type ConstraintConfig = Record<string, YearlyValues>;

////////////////////////////////////////////////////////////////
// Complex Configuration Types
////////////////////////////////////////////////////////////////

/**
 * Represents configuration for multiple clusters within each area.
 *
 * @example
 * {
 *   "Area1": {
 *     "Cluster1": { "0": 10, "1": "", "2": 30 },
 *     "Cluster2": { "0": 5, "1": 25, "2": "" }
 *   }
 * }
 */
export type ClustersConfig = Record<string, ClusterConfig | StorageConfig>;

/**
 * General configuration format for scenarios using single areas as elements.
 * Each scenario type maps to its specific areas configuration.
 *
 * @example
 * {
 *   "load": {
 *     "Area1": { "0": 15, "1": 255, "2": "", "3": "", "4": "", "5": "" },
 *     "Area2": { "0": 15, "1": 255, "2": "", "3": "", "4": "", "5": "" }
 *   }
 * }
 */
export type GenericScenarioConfig = Record<string, AreaConfig>;

/**
 * Full configuration format for scenarios involving multiple clusters per area.
 *
 * @example
 * {
 *   "thermal": {
 *     "Area1": {
 *       "Cluster1": { "0": 10, "1": "", "2": 30 },
 *       "Cluster2": { "0": 5, "1": 25, "2": "" }
 *     }
 *   }
 * }
 */
export type ClustersScenarioConfig = Record<string, ClustersConfig>;

/**
 * Configuration for storages with constraints.
 * Maps storage identifiers to their constraints configuration.
 *
 * @example
 * {
 *   "test storage": {
 *     "test3": { "1": 10, "2": "", "3": 30 },
 *     "discharge-limit": { "1": 5, "2": 25, "3": "" }
 *   }
 * }
 */
export type StorageConstraintsConfig = Record<string, ConstraintConfig>;

/**
 * Full configuration format for scenarios involving storage constraints per area.
 *
 * @example
 * {
 *   "shortTermStorageAdditionalConstraints": {
 *     "z1": {
 *       "test storage": {
 *         "test3": { "1": 10, "2": "", "3": 30 },
 *         "discharge-limit": { "1": 5, "2": 25, "3": "" }
 *       }
 *     }
 *   }
 * }
 */
export type StorageConstraintsScenarioConfig = Record<string, StorageConstraintsConfig>;

////////////////////////////////////////////////////////////////
// Handler Return Types
////////////////////////////////////////////////////////////////

export interface ClustersHandlerReturn {
  areas: string[];
  clusters: Record<string, ClustersConfig>;
}

export interface StorageConstraintsHandlerReturn {
  areas: string[];
  constraints: Record<string, GenericScenarioConfig>;
}

////////////////////////////////////////////////////////////////
// Main Configuration Interface
////////////////////////////////////////////////////////////////

export interface ScenarioConfig {
  load?: GenericScenarioConfig;
  thermal?: ClustersScenarioConfig;
  hydro?: GenericScenarioConfig;
  wind?: GenericScenarioConfig;
  solar?: GenericScenarioConfig;
  ntc?: GenericScenarioConfig;
  renewable?: ClustersScenarioConfig;
  hydroInitialLevels?: GenericScenarioConfig;
  bindingConstraints?: GenericScenarioConfig;
  hydroFinalLevels?: GenericScenarioConfig;
  shortTermStorageInflows?: ClustersScenarioConfig;
  shortTermStorageAdditionalConstraints?: StorageConstraintsScenarioConfig;
}

export type NonNullableRulesetConfig = {
  [K in keyof ScenarioConfig]-?: NonNullable<ScenarioConfig[K]>;
};

export interface HandlerReturnTypes {
  load: GenericScenarioConfig;
  thermal: ClustersHandlerReturn;
  hydro: GenericScenarioConfig;
  wind: GenericScenarioConfig;
  solar: GenericScenarioConfig;
  ntc: GenericScenarioConfig;
  renewable: ClustersHandlerReturn;
  hydroInitialLevels?: GenericScenarioConfig;
  bindingConstraints: GenericScenarioConfig;
  hydroFinalLevels: GenericScenarioConfig;
  shortTermStorageInflows: ClustersHandlerReturn;
  shortTermStorageAdditionalConstraints: StorageConstraintsHandlerReturn;
}

////////////////////////////////////////////////////////////////
// Utility Types
////////////////////////////////////////////////////////////////

/**
 * Helper type to determine the correct data structure for a scenario
 */
export type ScenarioDataStructure<T extends ScenarioType> = T extends SimpleScenarioType
  ? GenericScenarioConfig
  : T extends ClusterScenarioType
    ? ClustersScenarioConfig
    : T extends ConstraintScenarioType
      ? StorageConstraintsScenarioConfig
      : never;

/**
 * Configuration type that can be displayed in the table
 */
export type TableConfigType =
  | GenericScenarioConfig
  | ClustersHandlerReturn
  | StorageConstraintsHandlerReturn;

/**
 * Configuration type that has areas
 */
export type AreaBasedConfig = ClustersHandlerReturn | StorageConstraintsHandlerReturn;

////////////////////////////////////////////////////////////////
// Type Guards
////////////////////////////////////////////////////////////////

/**
 * Checks if a scenario type is a simple scenario (area -> values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario type is a simple scenario, false otherwise
 */
export function isSimpleScenario(type: ScenarioType): type is SimpleScenarioType {
  return SIMPLE_SCENARIOS.includes(type as SimpleScenarioType);
}

/**
 * Checks if a scenario type is a cluster scenario (area -> cluster -> values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario type is a cluster scenario, false otherwise
 */
export function isClusterScenario(type: ScenarioType): type is ClusterScenarioType {
  return CLUSTER_SCENARIOS.includes(type as ClusterScenarioType);
}

/**
 * Checks if a scenario type is a constraint scenario (area -> storage -> constraint -> values)
 *
 * @param type - The scenario type to check
 * @returns True if the scenario type is a constraint scenario, false otherwise
 */
export function isConstraintScenario(type: ScenarioType): type is ConstraintScenarioType {
  return CONSTRAINT_SCENARIOS.includes(type as ConstraintScenarioType);
}

/**
 * Checks if a scenario type has area-based structure
 *
 * @param type - The scenario type to check
 * @returns True if the scenario type has area-based structure, false otherwise
 */
export function hasAreaStructure(type: ScenarioType): boolean {
  return isClusterScenario(type) || isConstraintScenario(type);
}

/**
 * Type guard to check if configuration has areas structure
 *
 * @param config - The configuration to check
 * @returns True if the configuration has areas structure, false otherwise
 */
export function hasAreas(
  config: HandlerReturnTypes[keyof HandlerReturnTypes],
): config is AreaBasedConfig {
  return (
    config !== undefined &&
    "areas" in config &&
    Array.isArray(config.areas) &&
    config.areas.every((area) => typeof area === "string")
  );
}

/**
 * Type guard to check if configuration has clusters
 *
 * @param config - The configuration to check
 * @returns True if the configuration has clusters, false otherwise
 */
export function hasClusters(config: AreaBasedConfig): config is ClustersHandlerReturn {
  return "clusters" in config;
}

/**
 * Type guard to check if configuration has constraints
 *
 * @param config - The configuration to check
 * @returns True if the configuration has constraints, false otherwise
 */
export function hasConstraints(config: AreaBasedConfig): config is StorageConstraintsHandlerReturn {
  return "constraints" in config;
}

////////////////////////////////////////////////////////////////
// Scenario Configuration Mapping
////////////////////////////////////////////////////////////////

export interface ScenarioMetadata {
  type: "simple" | "cluster" | "constraint";
  hasAreas: boolean;
  apiEndpoint?: string;
}

/**
 * Configuration mapping for all scenario types
 * This centralizes the configuration for each scenario type
 */
export const SCENARIO_CONFIG: Record<ScenarioType, ScenarioMetadata> = {
  // Simple scenarios (area -> values)
  load: { type: "simple", hasAreas: false },
  hydro: { type: "simple", hasAreas: false },
  wind: { type: "simple", hasAreas: false },
  solar: { type: "simple", hasAreas: false },
  ntc: { type: "simple", hasAreas: false },
  hydroInitialLevels: { type: "simple", hasAreas: false },
  bindingConstraints: { type: "simple", hasAreas: false },
  hydroFinalLevels: { type: "simple", hasAreas: false },

  // Cluster scenarios (area -> cluster/storage -> values)
  thermal: { type: "cluster", hasAreas: true },
  renewable: { type: "cluster", hasAreas: true },
  shortTermStorageInflows: { type: "cluster", hasAreas: true },

  // Constraint scenarios (area -> storage -> constraint -> values)
  shortTermStorageAdditionalConstraints: { type: "constraint", hasAreas: true },
};

/**
 * Get scenario metadata for a given scenario type
 *
 * @param type - The scenario type to get metadata for
 * @returns The scenario metadata for the given type
 */
export function getScenarioMetadata(type: ScenarioType): ScenarioMetadata {
  return SCENARIO_CONFIG[type];
}

/**
 * Check if a scenario requires area selection
 *
 * @param type - The scenario type to check
 * @returns true if the scenario requires area selection, false otherwise
 */
export function requiresAreaSelection(type: ScenarioType): boolean {
  return SCENARIO_CONFIG[type].hasAreas;
}
