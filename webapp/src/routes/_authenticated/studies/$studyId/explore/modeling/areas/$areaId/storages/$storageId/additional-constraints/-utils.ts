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

import type { RouteListItem } from "@/components/page/ListView";
import type { QueryList } from "@/queries/types";
import { isQueryListItemOptimistic } from "@/queries/utils";
import type { StorageConstraint } from "@/services/api/studies/areas/storages/types";
import { sortByProp } from "@/services/utils";
import { linkOptions } from "@tanstack/react-router";

export function constraintsToList(constraints: QueryList<StorageConstraint>): RouteListItem[] {
  const list = constraints.map((constraint) => ({
    id: constraint.id,
    label: constraint.name,
    linkOptions: linkOptions({
      from: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints",
      to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId",
      params: { constraintId: constraint.id },
    }),
    loading: isQueryListItemOptimistic(constraint),
  }));

  return sortByProp("label", list);
}
