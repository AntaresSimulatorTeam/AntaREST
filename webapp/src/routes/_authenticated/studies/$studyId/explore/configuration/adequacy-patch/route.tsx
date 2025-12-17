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
  "/_authenticated/studies/$studyId/explore/configuration/adequacy-patch",
)({
  component: AdequacyPatchLayout,
});

function AdequacyPatchLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <TabsView
      tabs={[
        {
          id: "general",
          label: t("study.configuration.adequacyPatch.tab.general"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/adequacy-patch/general",
            params,
          }),
        },
        {
          id: "perimeter",
          label: t("study.configuration.adequacyPatch.tab.perimeter"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration/adequacy-patch/perimeter",
            params,
          }),
        },
      ]}
    />
  );
}
