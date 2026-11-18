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

import client from "@/services/api/client";
import { format } from "@/utils/stringUtils";
import { scenarioBuilderSchema, scenarioNameSchema, scenarioSchema } from "./schemas";
import type {
  CreateScenarioParams,
  DeleteScenarioParams,
  GetScenarioBuilderParams,
  UpdateScenarioParams,
} from "./types";

const URL = "/v1/studies/{studyId}/gems/scenario-builder";

export async function getScenarioBuilder({ studyId }: GetScenarioBuilderParams) {
  const { data } = await client.get(format(URL, { studyId }));
  return scenarioBuilderSchema.parse(data);
}

export async function createScenario({ studyId, scenarioName, value }: CreateScenarioParams) {
  const url = format(URL, { studyId });
  const { data } = await client.post(url, scenarioSchema.parse(value), {
    params: { scenario_name: scenarioNameSchema.parse(scenarioName) },
  });
  return scenarioSchema.parse(data);
}

export async function updateScenario({ studyId, scenarioName, value }: UpdateScenarioParams) {
  const url = format(URL, { studyId });
  const { data } = await client.put(url, scenarioSchema.parse(value), {
    params: { scenario_name: scenarioName },
  });
  return scenarioSchema.parse(data);
}

export async function deleteScenario({ studyId, scenarioName }: DeleteScenarioParams) {
  const url = format(URL, { studyId });
  await client.delete(url, { params: { scenarioName } });
}
