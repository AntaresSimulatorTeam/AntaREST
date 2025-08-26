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

import { adaptConstraintsDtoToFlattened } from "./adapters";
import type {
  ClustersHandlerReturn,
  ClustersScenarioConfig,
  GenericScenarioConfig,
  HandlerReturnTypes,
  NonNullableRulesetConfig,
  ScenarioConfig,
  StorageConstraintsHandlerReturn,
  StorageConstraintsScenarioConfig,
} from "./types";

////////////////////////////////////////////////////////////////
// Handlers
////////////////////////////////////////////////////////////////

type ConfigHandler<T, U = T> = (config: T) => U;

const handlers: {
  [K in keyof NonNullableRulesetConfig]: ConfigHandler<
    NonNullableRulesetConfig[K],
    HandlerReturnTypes[K]
  >;
} = {
  load: handleGenericConfig,
  thermal: handleClustersConfig,
  hydro: handleGenericConfig,
  wind: handleGenericConfig,
  solar: handleGenericConfig,
  ntc: handleGenericConfig,
  renewable: handleClustersConfig,
  hydroInitialLevels: handleGenericConfig,
  bindingConstraints: handleGenericConfig,
  hydroFinalLevels: handleGenericConfig,
  shortTermStorageInflows: handleClustersConfig,
  shortTermStorageAdditionalConstraints: handleStorageConstraintsConfig,
};

/**
 * Handles generic scenario configurations by reducing key-value pairs into a single object.
 *
 * @param config - The initial scenario configuration object.
 * @returns The processed configuration object.
 */
function handleGenericConfig(config: GenericScenarioConfig): GenericScenarioConfig {
  return Object.entries(config).reduce<GenericScenarioConfig>((acc, [areaId, yearlyValue]) => {
    acc[areaId] = yearlyValue;
    return acc;
  }, {});
}

/**
 * Processes clusters based configurations to separate areas and clusters.
 *
 * @param config - The initial clusters based scenario configuration.
 * @returns Object containing separated areas and cluster configurations.
 */
function handleClustersConfig(config: ClustersScenarioConfig): ClustersHandlerReturn {
  return Object.entries(config).reduce<ClustersHandlerReturn>(
    (acc, [areaId, clusterConfig]) => {
      acc.areas.push(areaId);
      acc.clusters[areaId] = clusterConfig;
      return acc;
    },
    { areas: [], clusters: {} },
  );
}

/**
 * Processes storage constraints configurations to flatten the structure.
 * Transforms the nested structure into a flat structure with "storageId - constraintId" keys.
 *
 * @param config - The initial storage constraints scenario configuration.
 * @returns Object containing separated areas and flattened constraints configurations.
 */
function handleStorageConstraintsConfig(
  config: StorageConstraintsScenarioConfig,
): StorageConstraintsHandlerReturn {
  return Object.entries(config).reduce<StorageConstraintsHandlerReturn>(
    (acc, [areaId, storageConfig]) => {
      acc.areas.push(areaId);
      // Use the adapter to flatten the nested structure
      acc.constraints[areaId] = adaptConstraintsDtoToFlattened(storageConfig);
      return acc;
    },
    { areas: [], constraints: {} },
  );
}

/**
 * Retrieves and processes the configuration for a specific scenario within a ruleset.
 *
 * @param config - Full configuration mapping by ruleset.
 * @param scenario - The specific scenario type to retrieve.
 * @returns The processed configuration or undefined if not found.
 */
export function getConfigByScenario<K extends keyof ScenarioConfig>(
  config: ScenarioConfig,
  scenario: K,
): HandlerReturnTypes[K] | undefined {
  const scenarioConfig = config[scenario];

  if (!scenarioConfig) {
    return undefined;
  }

  return handlers[scenario](scenarioConfig);
}
