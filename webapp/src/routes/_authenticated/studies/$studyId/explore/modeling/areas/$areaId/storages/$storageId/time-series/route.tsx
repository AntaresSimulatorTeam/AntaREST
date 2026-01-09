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
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series",
)({
  component: TimeSeriesLayout,
});

// !NOTE: The Matrix components are configured with `isTimeSeries={false}` and
// `customColumns={["TS 1"]}` as a temporary solution. These are actually
// time series matrices, but the development for them has not been completed
// on the simulator side yet. When that development is done, these properties
// should be removed to restore the standard time series behavior with resize
// functionality.

function TimeSeriesLayout() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();

  const matricesAllVersions = [
    {
      id: "modulation",
      label: t("study.modeling.storages.modulation"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/modulation",
        params,
      }),
    },
    {
      id: "rule-curves",
      label: t("study.modeling.storages.ruleCurves"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/rule-curves",
        params,
      }),
    },
    {
      id: "inflows",
      label: t("study.modeling.storages.inflows"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/inflows",
        params,
      }),
    },
  ];

  const matrices920 = [
    {
      id: "costs",
      label: t("study.modeling.storages.costs"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/costs",
        params,
      }),
    },
    {
      id: "variation-costs",
      label: t("study.modeling.storages.variationCosts"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/variation-costs",
        params,
      }),
    },
    {
      id: "level-cost",
      label: t("study.modeling.storages.levelCost"),
      linkOptions: linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/time-series/level-cost",
        params,
      }),
    },
  ];

  return (
    <TabsView
      tabs={[...matricesAllVersions, ...(semver.gte(study.version, "9.2.0") ? matrices920 : [])]}
    />
  );
}
