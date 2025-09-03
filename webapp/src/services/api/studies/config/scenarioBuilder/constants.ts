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

import type { ScenarioType } from "./types";

export const SCENARIOS = [
  "load",
  "thermal",
  "hydro",
  "wind",
  "solar",
  "ntc", // Since v8.2
  "renewable", // Since v8.1
  "hydroInitialLevels",
  "bindingConstraints", // Since v8.7
  "hydroFinalLevels", // Since v9.2
  "shortTermStorageInflows", // Since v9.3
  "shortTermStorageAdditionalConstraints", // Since v9.3
] as const;

// Scenarios with structure: area → yearly values
export const LEVEL1_SCENARIOS = [
  "load",
  "hydro",
  "wind",
  "solar",
  "ntc",
  "hydroInitialLevels",
  "bindingConstraints",
  "hydroFinalLevels",
] as const;

// Scenarios with structure: area → entity → yearly values
export const LEVEL2_SCENARIOS = ["thermal", "renewable", "shortTermStorageInflows"] as const;

// Scenarios with structure: area → entity → subentity → yearly values
export const LEVEL3_SCENARIOS = ["shortTermStorageAdditionalConstraints"] as const;

interface ScenarioMetadata {
  level: 1 | 2 | 3;
  requiresAreaSelection: boolean;
  minVersion?: number;
}

export const SCENARIO_METADATA: Record<ScenarioType, ScenarioMetadata> = {
  // Level 1 scenarios (area → values)
  load: { level: 1, requiresAreaSelection: false },
  hydro: { level: 1, requiresAreaSelection: false },
  wind: { level: 1, requiresAreaSelection: false },
  solar: { level: 1, requiresAreaSelection: false },
  ntc: { level: 1, requiresAreaSelection: false, minVersion: 820 },
  hydroInitialLevels: { level: 1, requiresAreaSelection: false },
  bindingConstraints: { level: 1, requiresAreaSelection: false, minVersion: 870 },
  hydroFinalLevels: { level: 1, requiresAreaSelection: false, minVersion: 920 },

  // Level 2 scenarios (area → entity → values)
  thermal: { level: 2, requiresAreaSelection: true },
  renewable: { level: 2, requiresAreaSelection: true, minVersion: 810 },
  shortTermStorageInflows: { level: 2, requiresAreaSelection: true, minVersion: 930 },

  // Level 3 scenarios (area → entity → subentity → values)
  shortTermStorageAdditionalConstraints: { level: 3, requiresAreaSelection: true, minVersion: 930 },
};
