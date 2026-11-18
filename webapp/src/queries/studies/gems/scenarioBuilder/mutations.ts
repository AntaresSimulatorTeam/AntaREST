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

import {
  createScenario,
  deleteScenario,
  updateScenario,
} from "@/services/api/studies/gems/scenarioBuilder";
import type {
  CreateScenarioParams,
  DeleteScenarioParams,
  UpdateScenarioParams,
} from "@/services/api/studies/gems/scenarioBuilder/types";
import type { Study } from "@/services/api/studies/types";
import { mutationOptions } from "@tanstack/react-query";
import { scenarioBuilderKeys } from "./keys";

export const scenarioBuilderMutations = {
  createScenario: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: scenarioBuilderKeys.createScenario(studyId),
      mutationFn: (params: Omit<CreateScenarioParams, "studyId">) => {
        return createScenario({ ...params, studyId });
      },
    });
  },
  updateScenario: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: scenarioBuilderKeys.updateScenario(studyId),
      mutationFn: (params: Omit<UpdateScenarioParams, "studyId">) => {
        return updateScenario({ ...params, studyId });
      },
    });
  },
  deleteScenario: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: scenarioBuilderKeys.deleteScenario(studyId),
      mutationFn: (params: Omit<DeleteScenarioParams, "studyId">) => {
        return deleteScenario({ ...params, studyId });
      },
    });
  },
};
