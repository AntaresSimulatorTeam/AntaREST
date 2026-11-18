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

import type { Study } from "@/services/api/studies/types";
import { studyKeys } from "../../keys";

export const scenarioBuilderKeys = {
  all: () => [...studyKeys.all(), "scenarioBuilders"],
  details: () => [...scenarioBuilderKeys.all(), "detail"],
  detail: (studyId: Study["id"]) => [...scenarioBuilderKeys.details(), { studyId }],
  createScenario: (studyId: Study["id"]) => [
    ...scenarioBuilderKeys.detail(studyId),
    "createScenario",
  ],
  updateScenario: (studyId: Study["id"]) => [
    ...scenarioBuilderKeys.detail(studyId),
    "updateScenario",
  ],
  deleteScenario: (studyId: Study["id"]) => [
    ...scenarioBuilderKeys.detail(studyId),
    "deleteScenario",
  ],
};
