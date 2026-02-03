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
import { useTranslation } from "react-i18next";
import semver from "semver";
import useStudy from "../../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/configuration")({
  component: ConfigurationLayout,
});

function ConfigurationLayout() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();

  return (
    <TabsView
      tabs={[
        {
          id: "general",
          label: "General",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/general",
            params,
          }),
        },
        {
          id: "ts-generation",
          label: "Time-Series Generation",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/ts-generation",
            params,
          }),
        },
        {
          id: "optimization",
          label: "Optimization",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/optimization",
            params,
          }),
        },
        semver.gte(study.version, "8.3.0") && {
          id: "adequacy-patch",
          label: "Adequacy Patch",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/adequacy-patch",
            params,
          }),
        },
        {
          id: "advanced-params",
          label: "Advanced Parameters",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/advanced-params",
            params,
          }),
        },
        semver.gte(study.version, "9.2.0") && {
          id: "compatibility",
          label: t("study.configuration.compatibility"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/compatibility",
            params,
          }),
        },
        {
          id: "eco-options",
          label: t("study.configuration.economicOpt"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/eco-options",
            params,
          }),
        },
        {
          id: "geo-trimming",
          label: t("study.configuration.geographicTrimming"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/geo-trimming",
            params,
          }),
        },
      ].filter(Boolean)}
    />
  );
}
