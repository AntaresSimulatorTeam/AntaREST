/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import Matrix from "@/components/Matrix";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId/time-series/availability",
)({
  component: Availability,
});

function Availability() {
  const { studyId, areaId, thermalId } = Route.useParams();

  return (
    <Matrix
      key={thermalId}
      studyId={studyId}
      url={`input/thermal/series/${areaId}/${thermalId}/series`}
      aggregateColumns="stats" // avg, min, max
    />
  );
}
