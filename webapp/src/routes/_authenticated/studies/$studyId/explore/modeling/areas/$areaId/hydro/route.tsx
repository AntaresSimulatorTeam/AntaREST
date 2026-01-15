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

import TabsView from "@/components/page/TabsView";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/Hydro",
)({
  component: HydroLayout,
});

function HydroLayout() {
  const params = Route.useParams();
  const study = useStudy();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      tabs={[
        {
          id: "managementOptions",
          label: "Management options",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/management-options",
            params,
          }),
        },
        {
          id: "inflowStructure",
          label: "Inflow structure",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/inflow-structure",
            params,
          }),
        },
        {
          id: "allocation",
          label: "Allocation",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/allocation",
            params,
          }),
        },
        {
          id: "correlation",
          label: "Correlation",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/correlation",
            params,
          }),
        },
        {
          id: "dailyPower&EnergyCredits",
          label: "Daily Power & Energy Credits",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/daily-power-and-energy-credits",
            params,
          }),
        },
        {
          id: "reservoirLevels",
          label: "Reservoir levels",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/reservoir-levels",
            params,
          }),
        },
        {
          id: "waterValues",
          label: "Water values",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/water-values",
            params,
          }),
        },
        {
          id: "hydroStorage",
          label: "Hydro Storage",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/hydro-storage",
            params,
          }),
        },
        {
          id: "runOfRiver",
          label: "Run of river",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/run-of-river",
            params,
          }),
        },
        semver.gte(study.version, "8.6.0") && {
          id: "minGen",
          label: "Min Gen",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro/min-gen",
            params,
          }),
        },
      ].filter(Boolean)}
    />
  );
}
