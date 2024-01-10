const AREA = "area";
const LINK = "link";
const CLUSTER = "cluster";
const RENEWABLE = "renewable";
const BINDING_CONSTRAINT = "binding constraint";

export const TABLE_MODE_TYPES = [
  AREA,
  LINK,
  CLUSTER,
  RENEWABLE,
  BINDING_CONSTRAINT,
] as const;

export const TABLE_MODE_COLUMNS_BY_TYPE = {
  [AREA]: [
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
  [LINK]: [
    "hurdlesCost",
    "loopFlow",
    "usePhaseShifter",
    "transmissionCapacities",
    "assetType",
    "linkStyle",
    "linkWidth",
    "displayComments",
    "filterSynthesis",
    "filterYearByYear",
  ],
  [CLUSTER]: [
    "group",
    "enabled",
    "mustRun",
    "unitCount",
    "nominalCapacity",
    "minStablePower",
    "spinning",
    "minUpTime",
    "minDownTime",
    "co2",
    "marginalCost",
    "fixedCost",
    "startupCost",
    "marketBidCost",
    "spreadCost",
    "tsGen",
    "volatilityForced",
    "volatilityPlanned",
    "lawForced",
    "lawPlanned",
  ],
  [RENEWABLE]: [
    "group",
    "tsInterpretation",
    "enabled",
    "unitCount",
    "nominalCapacity",
  ],
  [BINDING_CONSTRAINT]: ["type", "operator", "enabled"],
} as const;
