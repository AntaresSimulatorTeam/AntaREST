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
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId",
)({
  component: AreaLayout,
});

function AreaLayout() {
  const study = useStudy();
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <ViewWrapper>
      <TabsView
        tabs={[
          {
            id: "properties",
            label: t("study.modeling.properties"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/properties",
              params,
            }),
          },
          {
            id: "load",
            label: t("study.modeling.load"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/load",
              params,
            }),
          },
          {
            id: "thermals",
            label: t("study.modeling.thermals"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals",
              params,
            }),
          },
          semver.gte(study.version, "8.6.0") && {
            id: "storages",
            label: t("study.modeling.storages"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/storages",
              params,
            }),
          },
          {
            id: "renewables",
            label: t("study.modeling.renewables"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables",
              params,
            }),
            // pathSuffix: "renewables",
            // condition: renewablesClustering,
          },
          // { label: "study.modeling.hydro", pathSuffix: "hydro" },
          // {
          //   label: "study.modeling.wind",
          //   pathSuffix: "wind",
          //   condition: !renewablesClustering,
          // },
          // {
          //   label: "study.modeling.solar",
          //   pathSuffix: "solar",
          //   condition: !renewablesClustering,
          // },
          // { label: "study.modeling.reserves", pathSuffix: "reserves" },
          // { label: "study.modeling.miscGen", pathSuffix: "miscGen" },
        ].filter(Boolean)}
      />
    </ViewWrapper>
  );
}
