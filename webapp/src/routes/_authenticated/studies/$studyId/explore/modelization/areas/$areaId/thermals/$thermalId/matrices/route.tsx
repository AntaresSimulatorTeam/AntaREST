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
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices",
)({
  component: MatricesLayout,
});

function MatricesLayout() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      tabs={[
        {
          id: "common",
          label: t("study.modelization.clusters.matrix.common"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/common",
            params,
          }),
        },
        {
          id: "ts-generator",
          label: t("study.modelization.clusters.matrix.tsGen"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/ts-generator",
            params,
          }),
        },
        {
          id: "availability",
          label: t("study.modelization.clusters.matrix.availability"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/availability",
            params,
          }),
        },
        semver.gte(study.version, "8.7.0") && {
          id: "fuel-costs",
          label: t("study.modelization.clusters.matrix.fuelCost"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/fuel-cost",
            params,
          }),
        },
        semver.gte(study.version, "8.7.0") && {
          id: "co2-costs",
          label: t("study.modelization.clusters.matrix.co2Cost"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas/$areaId/thermals/$thermalId/matrices/co2-cost",
            params,
          }),
        },
      ].filter(Boolean)}
    />
  );
}
