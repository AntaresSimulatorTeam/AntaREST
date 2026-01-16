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

// !NOTE: Do not change the order of scenarios - this matches the order displayed in the UI
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
