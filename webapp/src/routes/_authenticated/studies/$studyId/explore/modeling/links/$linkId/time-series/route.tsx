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
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute, linkOptions, Outlet } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { TABS_VIEW_MIN_VERSION } from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId/time-series",
)({
  component: TimeSeriesLayout,
});

function TimeSeriesLayout() {
  const params = Route.useParams();
  const study = useStudy();
  const { t } = useTranslation();

  if (semver.lt(study.version, TABS_VIEW_MIN_VERSION)) {
    return <Outlet />;
  }

  return (
    <TabsView
      tabs={[
        {
          id: "parameters",
          label: t("study.modeling.links.matrix.parameters"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/links/$linkId/time-series/parameters",
            params,
          }),
        },
        {
          id: "capacities",
          label: t("study.modeling.links.matrix.capacities"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/links/$linkId/time-series/capacities",
            params,
          }),
        },
      ]}
    />
  );
}
