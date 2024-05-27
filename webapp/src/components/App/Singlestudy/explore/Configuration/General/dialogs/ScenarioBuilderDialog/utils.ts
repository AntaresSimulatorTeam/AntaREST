import { AxiosResponse } from "axios";
import { StudyMetadata } from "../../../../../../../../common/types";
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
  "bindingConstraints",
] as const;

export type ScenarioType = (typeof SCENARIOS)[number];

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

// Represents values that can be either a number or an uninitialized string (rand).
export type YearlyValues = number | "";
export type ElementConfig = Record<string, YearlyValues>;
// General configuration format for scenarios using areas as element IDs.
export type GenericScenarioConfig = Record<string, ElementConfig>;

export type ClusterConfig = Record<string, YearlyValues>;
export type AreaClustersConfig = Record<string, ClusterConfig>;
// Full configuration for scenarios involving multiple clusters per area.
export type ClustersScenarioConfig = Record<string, AreaClustersConfig>;

export interface ClustersHandlerReturn {
  areas: string[];
  clusters: Record<string, AreaClustersConfig>;
}

// General structure for ruleset configurations covering all scenarios.
export interface RulesetConfig {
  load?: GenericScenarioConfig;
  thermal?: ClustersScenarioConfig;
  hydro?: GenericScenarioConfig;
  wind?: GenericScenarioConfig;
  solar?: GenericScenarioConfig;
  ntc?: GenericScenarioConfig;
  renewable?: ClustersScenarioConfig;
  bindingConstraints?: GenericScenarioConfig;
}

type NonNullableRulesetConfig = {
  [K in keyof RulesetConfig]-?: NonNullable<RulesetConfig[K]>;
};

export type ScenarioBuilderConfig = Record<string, RulesetConfig>;

type ConfigHandler<T, U = T> = (config: T) => U;

export interface HandlerReturnTypes {
  load: GenericScenarioConfig;
  thermal: ClustersHandlerReturn;
  hydro: GenericScenarioConfig;
  wind: GenericScenarioConfig;
  solar: GenericScenarioConfig;
  ntc: GenericScenarioConfig;
  renewable: ClustersHandlerReturn;
  bindingConstraints: GenericScenarioConfig;
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
  bindingConstraints: handleGenericConfig,
};

/**
 * Handles generic scenario configurations by reducing key-value pairs into a single object.
 *
 * @param config The initial scenario configuration object.
 * @returns The processed configuration object.
 */
function handleGenericConfig(
  config: GenericScenarioConfig,
): GenericScenarioConfig {
  return Object.entries(config).reduce<GenericScenarioConfig>(
    (acc, [areaId, yearlyValue]) => {
      acc[areaId] = yearlyValue;
      return acc;
    },
    {},
  );
}

/**
 * Processes clusters based configurations to separate areas and clusters.
 *
 * @param config The initial clusters based scenario configuration.
 * @returns Object containing separated areas and cluster configurations.
 */
function handleClustersConfig(
  config: ClustersScenarioConfig,
): ClustersHandlerReturn {
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
 * Retrieves and processes the configuration for a specific scenario within a ruleset.
 *
 * @param config Full configuration mapping by ruleset.
 * @param scenario The specific scenario type to retrieve.
 * @returns The processed configuration or undefined if not found.
 */
export function getConfigByScenario<K extends keyof RulesetConfig>(
  config: RulesetConfig,
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

export async function getScenarioBuilderConfig(studyId: StudyMetadata["id"]) {
  const res = await client.get<ScenarioBuilderConfig>(
    `v1/studies/${studyId}/config/scenariobuilder`,
  );
  return res.data;
}

export async function getScenarioConfigByType(
  studyId: StudyMetadata["id"],
  scenarioType: ScenarioType,
) {
  const res = await client.get<ScenarioBuilderConfig>(
    `v1/studies/${studyId}/config/scenariobuilder`,
    {
      params: { scenarioType },
    },
  );
  return res.data;
}

export function updateScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  data: Partial<ScenarioBuilderConfig>,
) {
  return client.put<AxiosResponse<null, string>>(
    `v1/studies/${studyId}/config/scenariobuilder`,
    data,
  );
}
