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
import ViewWrapper from "@/components/page/ViewWrapper";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudySynthesis } from "@/redux/selectors";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import useArea from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-hooks/useArea";
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

  // Allow to display an appropriate error if the area does not exist
  useArea();

  // The value corresponds to the parameter "renewable-generation-modelling",
  // editable in "/studies/$studyId/explore/configuration/advanced-params"
  const enrModelling = useAppSelector((state) => getStudySynthesis(state, study.id)?.enr_modelling);

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
          semver.gte(study.version, "8.1.0") &&
            enrModelling === "clusters" && {
              id: "renewables",
              label: t("study.modeling.renewables"),
              linkOptions: linkOptions({
                to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables",
                params,
              }),
            },
          {
            id: "hydro",
            label: t("study.modeling.hydro"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/hydro",
              params,
            }),
          },
          enrModelling === "aggregated" && {
            id: "wind",
            label: t("study.modeling.wind"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/wind",
              params,
            }),
          },
          enrModelling === "aggregated" && {
            id: "solar",
            label: t("study.modeling.solar"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/solar",
              params,
            }),
          },
          // TODO: re-enable the version gate once reserve creation lands and v10
          // studies can be tested. Reserves is a v10+ feature, so the tab must be
          // hidden for studies under version 10.0.0.
          // semver.gte(study.version, "10.0.0") && {
          {
            id: "reserves",
            label: t("study.modeling.reserves"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/reserves",
              params,
            }),
          },
          {
            id: "miscGen",
            label: t("study.modeling.miscGen"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/areas/$areaId/misc-gen",
              params,
            }),
          },
        ].filter(Boolean)}
      />
    </ViewWrapper>
  );
}
