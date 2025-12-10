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

import ViewWrapper from "@/components/page/ViewWrapper";
import TabsView from "@/components/TabsView";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/configuration")({
  component: ConfigurationLayout,
});

const ADEQUACY_PATCH_TAB_ID = "adequacy-patch" as const;
const GEO_TRIMMING_TAB_ID = "geographic-trimming" as const;

function ConfigurationLayout() {
  const study = useStudy();
  const { t } = useTranslation();

  return (
    <TabsView
      items={[
        {
          label: "General",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/general",
            params: { studyId: study.id },
          }),
        },
        {
          label: "Time-Series Generation",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/ts-generation",
            params: { studyId: study.id },
          }),
        },
        {
          label: "Optimization",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/optimization",
            params: { studyId: study.id },
          }),
        },
        Number(study.version) >= 830 && {
          label: "Adequacy Patch",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/adequacy-patch",
            params: { studyId: study.id },
          }),
          id: ADEQUACY_PATCH_TAB_ID,
        },
        {
          label: "Advanced Parameters",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/advanced-params",
            params: { studyId: study.id },
          }),
        },
        {
          label: t("study.configuration.economicOpt"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/eco-options",
            params: { studyId: study.id },
          }),
        },
        {
          label: t("study.configuration.geographicTrimming"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/geo-trimming",
            params: { studyId: study.id },
          }),
          id: GEO_TRIMMING_TAB_ID,
        },
      ].filter(Boolean)}
      renderPanel={({ children }, tabId) => {
        if (tabId && [ADEQUACY_PATCH_TAB_ID, GEO_TRIMMING_TAB_ID].includes(tabId)) {
          return children;
        }
        return <ViewWrapper>{children}</ViewWrapper>;
      }}
    />
  );
}
