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

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore")({
  component: StudyExploreLayout,
});

function StudyExploreLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <TabsView
      tabs={[
        {
          id: "modeling",
          label: t("study.modeling"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling",
            params,
          }),
        },
        {
          id: "configuration",
          label: t("study.configuration"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration",
            params,
          }),
        },
        {
          id: "tablemode",
          label: t("study.tableMode"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/tablemode",
            params,
          }),
        },
        {
          id: "xpansion",
          label: "Xpansion",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/xpansion",
            params,
            search: { reload: undefined },
          }),
        },
        {
          id: "outputs",
          label: t("study.outputs"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/outputs",
            params,
          }),
        },
        {
          id: "debug",
          label: t("study.debug"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/debug",
            params,
            search: { path: undefined },
          }),
        },
      ]}
      divider
    />
  );
}
