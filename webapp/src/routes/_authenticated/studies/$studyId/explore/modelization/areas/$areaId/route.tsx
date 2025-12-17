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
import ViewWrapper from "@/components/page/ViewWrapper";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId",
)({
  component: AreaLayout,
});

function AreaLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <ViewWrapper>
      <TabsView
        tabs={[
          {
            id: "properties",
            label: t("study.modelization.properties"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modelization/areas/$areaId/properties",
              params,
            }),
          },
          {
            id: "load",
            label: t("study.modelization.load"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modelization/areas/$areaId/load",
              params,
            }),
          },
          {
            id: "thermal",
            label: t("study.modelization.thermal"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modelization/areas/$areaId/thermal",
              params,
            }),
          },
          // {
          //   label: "study.modelization.storages",
          //   pathSuffix: "storages",
          //   condition: semver.gte(study.version, "8.6.0"),
          // },
          // {
          //   label: "study.modelization.renewables",
          //   pathSuffix: "renewables",
          //   condition: renewablesClustering,
          // },
          // { label: "study.modelization.hydro", pathSuffix: "hydro" },
          // {
          //   label: "study.modelization.wind",
          //   pathSuffix: "wind",
          //   condition: !renewablesClustering,
          // },
          // {
          //   label: "study.modelization.solar",
          //   pathSuffix: "solar",
          //   condition: !renewablesClustering,
          // },
          // { label: "study.modelization.reserves", pathSuffix: "reserves" },
          // { label: "study.modelization.miscGen", pathSuffix: "miscGen" },
        ]}
      />
    </ViewWrapper>
  );
}
