/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { Options } from "@/components/fieldEditors/SelectFE";
import type { TableModeColumnsForType, TableModeType } from "@/services/api/tablemode/types";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

type TableModeColumnsByType = {
  [K in TableModeType]: TableModeColumnsForType<K>;
};

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

const TABLE_MODE_TYPES = [
  "areas",
  "links",
  "thermals",
  "renewables",
  "st-storages",
  "binding-constraints",
  "st-storages-additional-constraints",
] as const satisfies TableModeType[];

export const TABLE_MODE_COLUMNS_BY_TYPE = {
  areas: [
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
  links: [
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
  thermals: [
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
  renewables: [
    // Since v8.1
    "group",
    "enabled",
    "tsInterpretation",
    "unitCount",
    "nominalCapacity",
  ],
  "st-storages": [
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
    // Since v9.2
    "efficiencyWithdrawal",
    "penalizeVariationInjection",
    "penalizeVariationWithdrawal",
  ],
  "binding-constraints": [
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
  "st-storages-additional-constraints": [
    // Since v9.2
    "variable",
    "operator",
    "enabled",
  ],
} as const satisfies TableModeColumnsByType;

export const tableModeTypeOptions = TABLE_MODE_TYPES.map((type) => ({
  value: type,
  label: (t) => t(`tableMode.type.${type}`),
})) satisfies Options<TableModeType>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function getTableColumnsForType<T extends TableModeType>(type: T) {
  // Arrays have a numeric index signature because of `as const`
  return TABLE_MODE_COLUMNS_BY_TYPE[type];
}
