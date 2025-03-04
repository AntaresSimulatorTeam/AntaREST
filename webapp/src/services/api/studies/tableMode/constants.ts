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

const AREA = "areas";
const LINK = "links";
const THERMAL = "thermals";
const RENEWABLE = "renewables";
const ST_STORAGE = "st-storages";
const BINDING_CONSTRAINT = "binding-constraints";

export const TABLE_MODE_TYPES = [
  AREA,
  LINK,
  THERMAL,
  RENEWABLE,
  ST_STORAGE,
  BINDING_CONSTRAINT,
] as const;

// Deprecated types (breaking change from v2.16.8)
export const TABLE_MODE_TYPES_ALIASES = {
  area: AREA,
  link: LINK,
  cluster: THERMAL,
  renewable: RENEWABLE,
  "binding constraint": BINDING_CONSTRAINT,
};

export const TABLE_MODE_COLUMNS_BY_TYPE = {
  [AREA]: [
    "nonDispatchPower",
    "dispatchHydroPower",
    "otherDispatchPower",
    "energyCostUnsupplied",
    "spreadUnsuppliedEnergyCost",
    "energyCostSpilled",
    "spreadSpilledEnergyCost",
    "filterSynthesis",
    "filterByYear",
    // Since v8.3
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
    "comments",
    "displayComments",
    "filterSynthesis",
    "filterYearByYear",
  ],
  [THERMAL]: [
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
  [RENEWABLE]: [
    // Since v8.1
    "group",
    "enabled",
    "tsInterpretation",
    "unitCount",
    "nominalCapacity",
  ],
  [ST_STORAGE]: [
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
  [BINDING_CONSTRAINT]: [
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
