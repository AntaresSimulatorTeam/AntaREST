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

import { getBindingConstraints } from "@/services/api/studies/bindingConstraints";
import type { StudyMetadata } from "@/types/types";
import { queryListOptions } from "../utils";
import { bindingConstraintKeys } from "./keys";

export const bindingConstraintQueries = {
  list: (studyId: StudyMetadata["id"]) => {
    return queryListOptions({
      queryKey: bindingConstraintKeys.list(studyId),
      queryFn: () => getBindingConstraints({ studyId }),
    });
  },
};
