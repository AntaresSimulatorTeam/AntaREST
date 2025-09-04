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

import client from "@/services/api/client";
import { format } from "@/utils/stringUtils";
import { adaptScenarioDtoToForm, adaptScenarioFormToDto, getConfigByScenario } from "./adapters";
import type {
  GetScenarioBuilderFormParams,
  GetScenarioBuilderParams,
  ScenarioData,
  UpdateScenarioBuilderFormParams,
  UpdateScenarioBuilderParams,
} from "./types";

const URL = "/v1/studies/{studyId}/config/scenariobuilder/{scenarioType}";

export async function getScenarioBuilder({ studyId, scenarioType }: GetScenarioBuilderParams) {
  const { data } = await client.get<ScenarioData>(format(URL, { studyId, scenarioType }));
  return data;
}

export async function updateScenarioBuilder({
  studyId,
  scenarioType,
  values,
}: UpdateScenarioBuilderParams) {
  const { data } = await client.put<ScenarioData>(format(URL, { studyId, scenarioType }), values);
  return data;
}

export async function getScenarioBuilderForm({
  studyId,
  scenarioType,
}: GetScenarioBuilderFormParams) {
  const dto = await getScenarioBuilder({ studyId, scenarioType });
  return getConfigByScenario(dto, scenarioType);
}

export async function updateScenarioBuilderForm({
  studyId,
  scenarioType,
  values,
  areaId,
}: UpdateScenarioBuilderFormParams) {
  const adaptedValues = adaptScenarioFormToDto(scenarioType, values, areaId);
  const dto = await updateScenarioBuilder({ studyId, scenarioType, values: adaptedValues });
  return adaptScenarioDtoToForm(scenarioType, dto, areaId);
}
