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
  createBindingConstraint,
  deleteBindingConstraint,
  duplicateBindingConstraint,
  getBindingConstraints,
} from "@/services/api/studies/bindingConstraints";
import type { StudyMetadata } from "@/types/types";
import { mutationOptions, queryOptions } from "@tanstack/react-query";
import { studyQueries } from "./studies";
import { queryList } from "./utils";

export const bindingConstraintQueries = {
  all: () => [...studyQueries.all(), "bindingConstraints"] as const,
  list: (studyId: StudyMetadata["id"]) => {
    return queryOptions({
      queryKey: [...bindingConstraintQueries.all(), { studyId }],
      queryFn: async () => queryList(await getBindingConstraints({ studyId })),
      refetchOnWindowFocus: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnReconnect: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnMount: (query) => !query.state.data?.some((c) => c.isOptimistic),
    });
  },
};

export const bindingConstraintMutations = {
  all: bindingConstraintQueries.all,
  create: () => {
    return mutationOptions({
      mutationKey: [...bindingConstraintQueries.all(), "createBindingConstraint"],
      mutationFn: createBindingConstraint,
    });
  },
  duplicate: () => {
    return mutationOptions({
      mutationKey: [...bindingConstraintQueries.all(), "duplicateBindingConstraint"],
      mutationFn: duplicateBindingConstraint,
    });
  },
  delete: () => {
    return mutationOptions({
      mutationKey: [...bindingConstraintQueries.all(), "deleteBindingConstraint"],
      mutationFn: deleteBindingConstraint,
    });
  },
};
