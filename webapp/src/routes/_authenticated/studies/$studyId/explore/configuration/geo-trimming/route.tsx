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
  "/_authenticated/studies/$studyId/explore/configuration/geo-trimming",
)({
  component: GeographicTrimmingLayout,
});

function GeographicTrimmingLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <TabsView
      tabs={[
        {
          id: "areas",
          label: t("study.configuration.geographicTrimming.areas"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/geo-trimming/areas",
            params,
          }),
        },
        {
          id: "links",
          label: t("study.configuration.geographicTrimming.links"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/geo-trimming/links",
            params,
          }),
        },
        {
          id: "binding-constraints",
          label: t("study.configuration.geographicTrimming.bindingConstraints"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/geo-trimming/binding-constraints",
            params,
          }),
        },
      ]}
    />
  );
}
