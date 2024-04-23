const AREAS = "areas";
const LINKS = "links";
const THERMALS = "thermals";
const RENEWABLES = "renewables";
const ST_STORAGES = "st-storages";
const BINDING_CONSTRAINTS = "binding-constraints";

export const TABLE_MODE_TYPES = [
  AREAS,
  LINKS,
  THERMALS,
  RENEWABLES,
  BINDING_CONSTRAINTS,
] as const;

export const TABLE_MODE_COLUMNS_BY_TYPE = {
  [AREAS]: [
    // UI
    "colorRgb",
    // Optimization - Nodal optimization
    "nonDispatchablePower",
    "dispatchableHydroPower",
    "otherDispatchablePower",
    "averageUnsuppliedEnergyCost",
    "spreadUnsuppliedEnergyCost",
    "averageSpilledEnergyCost",
    "spreadSpilledEnergyCost",
    // Optimization - Filtering
    "filterSynthesis",
    "filterYearByYear",
    // Adequacy patch
    "adequacyPatchMode",
  ],
  [LINKS]: [
    "hurdlesCost",
    "loopFlow",
    "usePhaseShifter",
    "transmissionCapacities",
    "assetType",
    "linkStyle",
    "linkWidth",
    "comments", // unknown field?!
    "displayComments",
    // Optimization - Filtering
    "filterSynthesis",
    "filterYearByYear",
  ],
  [THERMALS]: [
    // "name" is read-only
    "group",
    "enabled",
    "unitCount",
    "nominalCapacity",
    "genTs",
    "minStablePower",
    "minUpTime",
    "minDownTime",
    "mustRun",
    "spinning",
    "volatilityForced",
    "volatilityPlanned",
    "lawForced",
    "lawPlanned",
    "marginalCost",
    "spreadCost",
    "fixedCost",
    "startupCost",
    "marketBidCost",
    // Pollutants - since v8.6 (except for "co2")
    "co2",
    "nh3",
    "so2",
    "nox",
    "pm25",
    "pm5",
    "pm10",
    "nmvoc",
    "op1",
    "op2",
    "op3",
    "op4",
    "op5",
    // Since v8.7
    "costGeneration",
    "efficiency",
    "variableOMCost",
  ],
  [RENEWABLES]: [
    "group",
    "enabled",
    "tsInterpretation",
    "unitCount",
    "nominalCapacity",
  ],
  [ST_STORAGES]: [
    "group",
    // "enabled",  // since v8.8
    "injectionNominalCapacity",
    "withdrawalNominalCapacity",
    "reservoirCapacity",
    "efficiency",
    "initialLevel",
    "initialLevelOptim",
  ],
  [BINDING_CONSTRAINTS]: [
    "group",
    "enabled",
    "timeStep",
    "operator",
    "comments",
    // Optimization - Filtering
    "filterSynthesis",
    "filterYearByYear",
  ],
} as const;
