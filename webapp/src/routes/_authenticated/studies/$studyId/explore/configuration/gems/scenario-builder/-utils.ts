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

import type { Scenario, ScenarioBuilder } from "@/services/api/studies/gems/scenarioBuilder/types";
import * as R from "ramda";

export function adaptScenarioBuilderToGridForm(scenarioBuilder: ScenarioBuilder) {
  const { scenarios } = scenarioBuilder;

  return R.mapObjIndexed((scenario) => {
    return scenario.reduce(
      (acc, value) => {
        acc[value.scenario.toString()] = value.timeSeriesIndex;
        return acc;
      },
      {} as Record<string, number>,
    );
  }, scenarios);
}

export function adaptScenarioFormToScenarioDto(scenarioForm: Record<string, number>): Scenario {
  return Object.entries(scenarioForm).map(([scenario, timeSeriesIndex]) => ({
    scenario: Number(scenario),
    timeSeriesIndex,
  }));
}

export type ScenarioBuilderGridForm = ReturnType<typeof adaptScenarioBuilderToGridForm>;
