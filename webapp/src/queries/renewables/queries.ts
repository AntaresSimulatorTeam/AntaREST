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

import { getRenewableClusters } from "@/services/api/studies/areas/renewables";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { EXTERNALLY_MUTATED, queryListOptions } from "../utils";
import { renewableKeys } from "./keys";

export const renewableQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryListOptions({
      queryKey: renewableKeys.list(studyId, areaId),
      queryFn: () => getRenewableClusters({ studyId, areaId }),
      // TODO: keep it stale until we update all writers to invalidate it.
      ...EXTERNALLY_MUTATED,
    });
  },
};
