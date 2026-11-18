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

import type z from "zod";
import { scenarioBuilderSchema, scenarioSchema } from "./schemas";

export type Scenario = z.infer<typeof scenarioSchema>;

export type ScenarioBuilder = z.infer<typeof scenarioBuilderSchema>;

////////////////////////////////////////////////////////////////
// Request Params
////////////////////////////////////////////////////////////////

export interface GetScenarioBuilderParams {
  studyId: string;
}

export interface ScenarioParams {
  studyId: string;
  scenarioName: string;
}

export interface CreateScenarioParams extends ScenarioParams {
  value: Scenario;
}

export interface UpdateScenarioParams extends ScenarioParams {
  value: Scenario;
}

export type DeleteScenarioParams = ScenarioParams;
