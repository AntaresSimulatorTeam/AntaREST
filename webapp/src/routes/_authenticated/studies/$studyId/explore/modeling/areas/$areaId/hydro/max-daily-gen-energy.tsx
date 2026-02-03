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

import { createFileRoute } from "@tanstack/react-router";
import HydroMatrix from "./-components/HydroMatrix";
import { HydroMatrixType } from "./-utils";
import { checkRouteAvailability } from "@/utils/routerUtils";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/max-daily-gen-energy",
)({
  component: MaxDailyGenEnergy,
});

function MaxDailyGenEnergy() {
  const study = useStudy();

    checkRouteAvailability({
      studyVersion: study.version,
      minVersion: "9.2.0",
      routePath: Route.path,
    });
  return <HydroMatrix type={HydroMatrixType.MaxDailyGenEnergy} />;
}
