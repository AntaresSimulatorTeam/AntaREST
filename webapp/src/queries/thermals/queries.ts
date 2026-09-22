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

import { getThermalClusters } from "@/services/api/studies/areas/thermals";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { EXTERNALLY_MUTATED, queryListOptions } from "../utils";
import { thermalKeys } from "./keys";

export const thermalQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryListOptions({
      queryKey: thermalKeys.list(studyId, areaId),
      queryFn: () => getThermalClusters({ studyId, areaId }),
      // TODO(PR2): select details from this list; keep it stale until all writers invalidate it.
      ...EXTERNALLY_MUTATED,
    });
  },
};
