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

import { storageQueries } from "@/queries/storages";
import { sortByName } from "@/services/utils";
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/",
)({
  beforeLoad: async ({ context, params: { studyId, areaId, storageId } }) => {
    const constraints = await context.queryClient.ensureQueryData(
      storageQueries.constraintList(studyId, areaId, storageId),
    );

    if (constraints.length > 0) {
      throw redirect({
        from: Route.fullPath,
        to: "$constraintId",
        params: { constraintId: sortByName(constraints)[0].id },
      });
    }
  },
});
