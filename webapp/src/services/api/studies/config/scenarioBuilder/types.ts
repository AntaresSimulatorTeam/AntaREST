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

import type { LEVEL1_SCENARIOS, LEVEL2_SCENARIOS, LEVEL3_SCENARIOS, SCENARIOS } from "./constants";

export type ScenarioType = (typeof SCENARIOS)[number];
export type Level1ScenarioType = (typeof LEVEL1_SCENARIOS)[number];
export type Level2ScenarioType = (typeof LEVEL2_SCENARIOS)[number];
export type Level3ScenarioType = (typeof LEVEL3_SCENARIOS)[number];

/**
 * Yearly configuration values, either a number or uninitialized ("rand")
 *
 * @example { "0": 120, "1": "", "2": 150 }
 */
export type YearlyValues = number | "";

/**
 * Maps entity identifiers to their yearly values
 *
 * @example { "Area1": { "0": 10, "1": 20, "2": "" } }
 */
export type EntityYearlyValues = Record<string, YearlyValues>;

/**
 * Level 1: Area → Yearly Values
 *
 * @example { "Area1": { "0": 10, "1": 20 }, "Area2": { "0": 30, "1": 40 } }
 */
export type Level1Data = Record<string, EntityYearlyValues>;

/**
 * Level 2: Area → Entity → Yearly Values
 *
 * @example { "Area1": { "Entity1": { "0": 10 }, "Entity2": { "1": 20 } } }
 */
export type Level2Data = Record<string, Record<string, EntityYearlyValues>>;

/**
 * Level 3: Area → Entity → SubEntity → Yearly Values
 *
 * @example { "Area1": { "Entity1": { "SubEntity1": { "0": 10 } } } }
 */
export type Level3Data = Record<string, Record<string, Record<string, EntityYearlyValues>>>;

export interface ScenarioData {
  load?: Level1Data;
  thermal?: Level2Data;
  hydro?: Level1Data;
  wind?: Level1Data;
  solar?: Level1Data;
  ntc?: Level1Data;
  renewable?: Level2Data;
  hydroInitialLevels?: Level1Data;
  bindingConstraints?: Level1Data;
  hydroFinalLevels?: Level1Data;
  shortTermStorageInflows?: Level2Data;
  shortTermStorageAdditionalConstraints?: Level3Data;
}

export type NonNullableScenarioData = {
  [K in keyof ScenarioData]-?: NonNullable<ScenarioData[K]>;
};

// Maps scenario type to its appropriate data structure
export type ScenarioDataStructure<T extends ScenarioType> = T extends Level1ScenarioType
  ? Level1Data
  : T extends Level2ScenarioType
    ? Level2Data
    : T extends Level3ScenarioType
      ? Level3Data
      : never;
