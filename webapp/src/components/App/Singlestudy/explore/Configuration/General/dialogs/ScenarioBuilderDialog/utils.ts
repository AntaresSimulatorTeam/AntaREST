import { AxiosResponse } from "axios";
import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

// Defines each scenario type and its corresponding symbol.
export const SCENARIOS = [
  { type: "load", symbol: "l" },
  { type: "thermal", symbol: "t" },
  { type: "hydro", symbol: "h" },
  { type: "wind", symbol: "w" },
  { type: "solar", symbol: "s" },
  { type: "ntc", symbol: "ntc" },
  { type: "hydroLevels", symbol: "r" },
  { type: "bindingConstraints", symbol: "bc" },
] as const;

// Maps scenario types to the row types used in user interfaces.
export const ROW_TYPE_BY_SCENARIO = {
  load: "area",
  thermal: "area",
  hydro: "area",
  wind: "area",
  solar: "area",
  ntc: "link",
  hydroLevels: "area",
  bindingConstraints: "constraintGroup",
} as const;

export const RULESET_PATH =
  "settings/generaldata/general/active-rules-scenario";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type RowType = keyof typeof ROW_TYPE_BY_SCENARIO;
export type ScenarioType = (typeof SCENARIOS)[number]["type"];
export type ScenarioSymbol = (typeof SCENARIOS)[number]["symbol"];

// Represents values that can be either a number or an uninitialized string.
export type YearlyValues = number | "";

// Maps element IDs to their configurations, consisting of yearly data.
export type ElementConfig = Record<string, YearlyValues>;
// General configuration format for scenarios using areas as element IDs.
export type GenericScenarioConfig = Record<string, ElementConfig>;

// Configuration format for clusters within thermal scenarios.
export type ClusterConfig = Record<string, YearlyValues>;
// Maps area IDs to configurations of clusters within those areas.
export type AreaClustersConfig = Record<string, ClusterConfig>; // TODO make name more generic
// Full configuration for thermal scenarios involving multiple clusters per area.
export type ThermalConfig = Record<string, AreaClustersConfig>;

// Return structure for thermal scenario configuration handling.
export interface ThermalHandlerReturn {
  areas: string[];
  clusters: Record<string, AreaClustersConfig>;
}

// General structure for ruleset configurations covering all scenarios.
export interface RulesetConfig {
  l?: GenericScenarioConfig;
  h?: GenericScenarioConfig;
  s?: GenericScenarioConfig;
  w?: GenericScenarioConfig;
  t?: ThermalConfig;
  ntc?: GenericScenarioConfig;
  r?: ThermalConfig;
  bc?: GenericScenarioConfig;
}

// Enforces that all configurations within a ruleset are non-nullable.
type NonNullableRulesetConfig = {
  [K in keyof RulesetConfig]-?: NonNullable<RulesetConfig[K]>;
};

// Maps ruleset names to their corresponding configurations.
export type ScenarioBuilderConfig = Record<string, RulesetConfig>;

// Function type for configuration handlers, capable of transforming config types.
type ConfigHandler<T, U = T> = (config: T) => U;

// Specific return types for each scenario handler.
export interface HandlerReturnTypes {
  l: GenericScenarioConfig;
  h: GenericScenarioConfig;
  s: GenericScenarioConfig;
  w: GenericScenarioConfig;
  r: ThermalHandlerReturn;
  ntc: GenericScenarioConfig;
  t: ThermalHandlerReturn;
  bc: GenericScenarioConfig;
}

// Configuration handlers mapped by scenario type.
const handlers: {
  [K in keyof NonNullableRulesetConfig]: ConfigHandler<
    NonNullableRulesetConfig[K],
    HandlerReturnTypes[K]
  >;
} = {
  l: handleGenericConfig,
  h: handleGenericConfig,
  s: handleGenericConfig,
  w: handleGenericConfig,
  r: handleThermalConfig,
  ntc: handleGenericConfig,
  bc: handleGenericConfig,
  t: handleThermalConfig,
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
 * Processes thermal configurations to separate areas and clusters.
 *
 * @param config The initial thermal scenario configuration.
 * @returns Object containing separated areas and cluster configurations.
 */
function handleThermalConfig(config: ThermalConfig): ThermalHandlerReturn {
  return Object.entries(config).reduce<ThermalHandlerReturn>(
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
 * @param ruleset The name of the ruleset to query.
 * @param scenario The specific scenario type to retrieve.
 * @returns The processed configuration or undefined if not found.
 */
export function getConfigByScenario<K extends keyof RulesetConfig>(
  config: ScenarioBuilderConfig,
  ruleset: string,
  scenario: K,
): HandlerReturnTypes[K] | undefined {
  const scenarioConfig = config[ruleset]?.[scenario];

  if (!scenarioConfig) {
    return undefined;
  }

  return handlers[scenario](scenarioConfig);
}

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/scenariobuilder`;
}

export async function getScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
): Promise<ScenarioBuilderConfig> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function updateScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  data: Partial<ScenarioBuilderConfig>,
): Promise<AxiosResponse<null, string>> {
  return client.put(makeRequestURL(studyId), data);
}
