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
import { queryOptions } from "@tanstack/react-query";
import { queryList } from "../utils";
import { bindingConstraintKeys } from "./keys";

export const bindingConstraintQueries = {
  list: (studyId: StudyMetadata["id"]) => {
    return queryOptions({
      queryKey: bindingConstraintKeys.list(studyId),
      queryFn: async () => queryList(await getBindingConstraints({ studyId })),
      refetchOnWindowFocus: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnReconnect: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnMount: (query) => !query.state.data?.some((c) => c.isOptimistic),
    });
  },
};
