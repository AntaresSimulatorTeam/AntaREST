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

import type { AxiosResponse } from "axios";
import type { StudyMetadata } from "../../../../../../../../types/types";
import client from "../../../../../../../../services/api/client";

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
  "shortTermStorage", // Since v9.3
] as const;

export type ScenarioType = (typeof SCENARIOS)[number];

////////////////////////////////////////////////////////////////
// Types
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
export type ByAreaConfig = Record<string, ClusterConfig | StorageConfig>;

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
export type TwoLevelScenarioConfig = Record<string, ByAreaConfig>;

export interface TwoLevelHandlerReturn {
  areas: string[];
  clusters: Record<string, ByAreaConfig>;
}

// General structure for ruleset configurations covering all scenarios.
export interface ScenarioConfig {
  load?: GenericScenarioConfig;
  thermal?: TwoLevelScenarioConfig;
  hydro?: GenericScenarioConfig;
  wind?: GenericScenarioConfig;
  solar?: GenericScenarioConfig;
  ntc?: GenericScenarioConfig;
  renewable?: TwoLevelScenarioConfig;
  hydroInitialLevels?: GenericScenarioConfig;
  bindingConstraints?: GenericScenarioConfig;
  hydroFinalLevels?: GenericScenarioConfig;
  shortTermStorage?: TwoLevelScenarioConfig;
}

type NonNullableRulesetConfig = {
  [K in keyof ScenarioConfig]-?: NonNullable<ScenarioConfig[K]>;
};

type ConfigHandler<T, U = T> = (config: T) => U;

export interface HandlerReturnTypes {
  load: GenericScenarioConfig;
  thermal: TwoLevelHandlerReturn;
  hydro: GenericScenarioConfig;
  wind: GenericScenarioConfig;
  solar: GenericScenarioConfig;
  ntc: GenericScenarioConfig;
  renewable: TwoLevelHandlerReturn;
  hydroInitialLevels?: GenericScenarioConfig;
  bindingConstraints: GenericScenarioConfig;
  hydroFinalLevels: GenericScenarioConfig;
  shortTermStorage: TwoLevelHandlerReturn;
}

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
  shortTermStorage: handleClustersConfig,
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
function handleClustersConfig(config: TwoLevelScenarioConfig): TwoLevelHandlerReturn {
  return Object.entries(config).reduce<TwoLevelHandlerReturn>(
    (acc, [areaId, clusterConfig]) => {
      acc.areas.push(areaId);
      acc.clusters[areaId] = clusterConfig;
      return acc;
    },
    { areas: [], clusters: {} },
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

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getScenarioConfigByType(
  studyId: StudyMetadata["id"],
  scenarioType: ScenarioType,
) {
  const res = await client.get<ScenarioConfig>(
    `v1/studies/${studyId}/config/scenariobuilder/${scenarioType}`,
  );
  return res.data;
}

export function updateScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  data: Partial<ScenarioConfig>,
  scenarioType: ScenarioType,
) {
  return client.put<AxiosResponse<null, string>>(
    `v1/studies/${studyId}/config/scenariobuilder/${scenarioType}`,
    data,
  );
}
