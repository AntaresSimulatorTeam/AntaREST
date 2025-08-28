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

import { nestedStructureToFlattened } from "./adapters";
import type {
  Level1Data,
  Level2Data,
  Level2Display,
  Level3Data,
  Level3Display,
  NonNullableScenarioData,
  ScenarioData,
  ScenarioDisplayMap,
} from "./types";

////////////////////////////////////////////////////////////////
// Data Processors
////////////////////////////////////////////////////////////////

type DataProcessor<T, U = T> = (data: T) => U;

const processors: {
  [K in keyof NonNullableScenarioData]: DataProcessor<
    NonNullableScenarioData[K],
    ScenarioDisplayMap[K]
  >;
} = {
  load: processLevel1Data,
  thermal: processLevel2Data,
  hydro: processLevel1Data,
  wind: processLevel1Data,
  solar: processLevel1Data,
  ntc: processLevel1Data,
  renewable: processLevel2Data,
  hydroInitialLevels: processLevel1Data,
  bindingConstraints: processLevel1Data,
  hydroFinalLevels: processLevel1Data,
  shortTermStorageInflows: processLevel2Data,
  shortTermStorageAdditionalConstraints: processLevel3Data,
};

/**
 * Processes Level 1 data (direct area to yearly values)
 *
 * @param data - The Level 1 data from API
 * @returns The processed Level 1 display data
 */
function processLevel1Data(data: Level1Data): Level1Data {
  return Object.entries(data).reduce<Level1Data>((acc, [areaId, yearlyValue]) => {
    acc[areaId] = yearlyValue;
    return acc;
  }, {});
}

/**
 * Processes Level 2 data (area → entity → yearly values)
 * Extracts areas and organizes entities by area
 *
 * @param data - The Level 2 data from API
 * @returns Object with areas list and entity configurations
 */
function processLevel2Data(data: Level2Data): Level2Display {
  return Object.entries(data).reduce<Level2Display>(
    (acc, [areaId, entityConfig]) => {
      acc.areas.push(areaId);
      acc.entities[areaId] = entityConfig;
      return acc;
    },
    { areas: [], entities: {} },
  );
}

/**
 * Processes Level 3 data (area → entity → subentity → yearly values)
 * Extracts areas and flattens the nested structure for UI display
 *
 * @param data - The Level 3 data from API
 * @returns Object with areas list and flattened entity configurations
 */
function processLevel3Data(data: Level3Data): Level3Display {
  return Object.entries(data).reduce<Level3Display>(
    (acc, [areaId, entityConfig]) => {
      acc.areas.push(areaId);
      // Flatten the nested structure for UI display
      acc.flattenedEntities[areaId] = nestedStructureToFlattened(entityConfig);
      return acc;
    },
    { areas: [], flattenedEntities: {} },
  );
}

/**
 * Retrieves and processes the configuration for a specific scenario type
 *
 * @param data - Full scenario data from API
 * @param scenario - The specific scenario type to process
 * @returns The processed display data or undefined if not found
 */
export function getConfigByScenario<K extends keyof ScenarioData>(
  data: ScenarioData,
  scenario: K,
): ScenarioDisplayMap[K] | undefined {
  const scenarioData = data[scenario];

  if (!scenarioData) {
    return undefined;
  }

  return processors[scenario](scenarioData);
}
