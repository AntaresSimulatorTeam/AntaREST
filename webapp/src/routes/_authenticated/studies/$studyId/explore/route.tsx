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

import TabsView from "@/components/TabsView";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore")({
  component: StudyExploreLayout,
});

{
  /* <TabWrapper
  study={study}
  divider
  tabList={[
    {
      label: t("study.modelization"),
      path: `/studies/${studyId}/explore/modelization`,
    },
    {
      label: t("study.configuration"),
      path: `/studies/${studyId}/explore/configuration`,
    },
    {
      label: t("study.tableMode"),
      path: `/studies/${studyId}/explore/tablemode`,
    },
    { label: "Xpansion", path: `/studies/${studyId}/explore/xpansion` },
    {
      label: t("study.results"),
      path: `/studies/${studyId}/explore/results`,
    },
    {
      label: t("study.debug"),
      path: `/studies/${studyId}/explore/debug`,
    },
  ]}
  disablePadding
/> */
}

function StudyExploreLayout() {
  const study = useStudy();
  const { t } = useTranslation();

  return (
    <TabsView
      items={[
        {
          label: t("study.tableMode"),
          linkOptions: {
            to: "/studies/$studyId/explore/tablemode",
            params: { studyId: study.id },
          },
        },
      ]}
    />
  );
}
