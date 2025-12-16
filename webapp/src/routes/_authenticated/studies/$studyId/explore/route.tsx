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
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../../../-shared/hook/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore")({
  component: StudyExploreLayout,
});

function StudyExploreLayout() {
  const study = useStudy();
  const { t } = useTranslation();

  return (
    <TabsView
      tabs={[
        {
          id: "modelization",
          label: t("study.modelization"),
          linkOptions: {
            to: "/studies/$studyId/explore/modelization",
            params: { studyId: study.id },
          },
        },
        {
          id: "configuration",
          label: t("study.configuration"),
          linkOptions: {
            to: "/studies/$studyId/explore/configuration",
            params: { studyId: study.id },
          },
        },
        {
          id: "tablemode",
          label: t("study.tableMode"),
          linkOptions: {
            to: "/studies/$studyId/explore/tablemode",
            params: { studyId: study.id },
          },
        },
        {
          id: "xpansion",
          label: "Xpansion",
          linkOptions: {
            to: "/studies/$studyId/explore/xpansion",
            params: { studyId: study.id },
          },
        },
        {
          id: "outputs",
          label: t("study.results"),
          linkOptions: {
            to: "/studies/$studyId/explore/outputs",
            params: { studyId: study.id },
          },
        },
        {
          id: "debug",
          label: t("study.debug"),
          linkOptions: {
            to: "/studies/$studyId/explore/debug",
            params: { studyId: study.id },
          },
        },
      ]}
      divider
    />
  );
}
