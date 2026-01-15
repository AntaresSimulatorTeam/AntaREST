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
import { createFileRoute, linkOptions } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro",
)({
  component: HydroLayout,
});

function HydroLayout() {
  const params = Route.useParams();

  // const tabList = useMemo(() => {
  //   const basePath = `/studies/${study?.id}/explore/modelization/area/${encodeURI(areaId)}/hydro`;

  //   return [
  //     { label: "Inflow structure", path: `${basePath}/inflow-structure` },
  //     { label: "Allocation", path: `${basePath}/allocation` },
  //     { label: "Correlation", path: `${basePath}/correlation` },
  //     {
  //       label: "Daily Power & Energy Credits",
  //       path: `${basePath}/dailypower&energy`,
  //     },
  //     { label: "Reservoir levels", path: `${basePath}/reservoirlevels` },
  //     { label: "Water values", path: `${basePath}/watervalues` },
  //     { label: "Hydro Storage", path: `${basePath}/hydrostorage` },
  //     { label: "Run of river", path: `${basePath}/ror` },
  //     semver.gte(study.version, "8.6.0") && { label: "Min Gen", path: `${basePath}/mingen` },
  //   ].filter(Boolean);
  // }, [areaId, study?.id, study.version]);

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
      ]}
    />
  );
}
