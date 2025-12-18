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

import TabsView from "@/components/page/TabsView";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId",
)({
  component: ThermalLayout,
});

function ThermalLayout() {
  const params = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      onBack={linkOptions({
        to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals",
        params,
      })}
      divider
      tabs={[
        {
          id: "parameters",
          label: t("study.modelization.thermals.parameters"),
          linkOptions: {
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/parameters",
            params,
          },
        },
        {
          id: "time-series",
          label: t("global.timeSeries"),
          linkOptions: {
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/time-series",
            params,
          },
        },
      ]}
    />
  );
}
