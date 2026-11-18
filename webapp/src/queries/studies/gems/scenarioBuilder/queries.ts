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

import { getScenarioBuilder } from "@/services/api/studies/gems/scenarioBuilder";
import type { Study } from "@/services/api/studies/types";
import { queryOptions } from "@tanstack/react-query";
import { scenarioBuilderKeys } from "./keys";

export const scenarioBuilderQueries = {
  detail: (studyId: Study["id"]) => {
    return queryOptions({
      queryKey: scenarioBuilderKeys.detail(studyId),
      queryFn: () => getScenarioBuilder({ studyId }),
    });
  },
};
