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
    "nonDispatchablePower",
    "dispatchableHydroPower",
    "otherDispatchablePower",
    "averageUnsuppliedEnergyCost",
    "spreadUnsuppliedEnergyCost",
    "averageSpilledEnergyCost",
    "spreadSpilledEnergyCost",
    "filterSynthesis",
    "filterYearByYear",
    // Since v8.3
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
    "comments",
    "displayComments",
    "filterSynthesis",
    "filterYearByYear",
  ],
  [THERMALS]: [
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
    "co2",
    // Since v8.6
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
    // Since v8.1
    "group",
    "enabled",
    "tsInterpretation",
    "unitCount",
    "nominalCapacity",
  ],
  [ST_STORAGES]: [
    // Since v8.6
    "group",
    "injectionNominalCapacity",
    "withdrawalNominalCapacity",
    "reservoirCapacity",
    "efficiency",
    "initialLevel",
    "initialLevelOptim",
    // Since v8.8
    "enabled",
  ],
  [BINDING_CONSTRAINTS]: [
    "enabled",
    "timeStep",
    "operator",
    "comments",
    // Since v8.3
    "filterSynthesis",
    "filterYearByYear",
    // Since v8.7
    "group",
  ],
} as const;
