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

import { tableModeQueries } from "@/queries/tableMode/queries";
import { sortByName } from "@/services/utils";
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/table-modes/")({
  beforeLoad: async ({ context }) => {
    const tableModes = await context.queryClient.ensureQueryData(tableModeQueries.list());

    if (tableModes.length > 0) {
      throw redirect({
        from: Route.fullPath,
        to: "$tableModeId",
        params: { tableModeId: sortByName(tableModes)[0].id },
      });
    }
  },
});
