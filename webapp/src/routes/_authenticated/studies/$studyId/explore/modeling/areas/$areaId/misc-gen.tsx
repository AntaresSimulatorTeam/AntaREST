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

import Matrix from "@/components/Matrix";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/misc-gen",
)({
  component: MiscGen,
});

const COLUMNS = [
  "CHP",
  "Bio Mass",
  "Bio Gaz",
  "Waste",
  "GeoThermal",
  "Other",
  "PSP",
  "ROW Balance",
] as const;

function MiscGen() {
  const { studyId, areaId } = Route.useParams();
  const url = `input/misc-gen/miscgen-${areaId}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Matrix
      key={areaId}
      studyId={studyId}
      url={url}
      customColumns={COLUMNS}
      aggregateColumns={["total"]}
      isTimeSeries={false}
      enableFilters
    />
  );
}
