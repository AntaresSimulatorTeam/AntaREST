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
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { compactSemanticVersion } from "@/utils/versionUtils";
import { createFileRoute } from "@tanstack/react-router";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId/time-series/fuel-cost",
)({
  component: FuelCost,
});

function FuelCost() {
  const study = useStudy();
  const area = useArea();
  const { thermalId } = Route.useParams();
  const minVersion = "8.7.0";

  if (semver.lt(study.version, minVersion)) {
    throw new Error(
      `Fuel Cost matrix is only available for study version ${compactSemanticVersion(minVersion)} and above.`,
    );
  }

  return (
    <Matrix
      key={thermalId}
      studyId={study.id}
      url={`input/thermal/series/${area.id}/${thermalId}/fuelCost`}
    />
  );
}
