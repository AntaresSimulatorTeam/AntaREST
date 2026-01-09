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
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId",
)({
  component: LinkLayout,
});

function LinkLayout() {
  const params = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <TabsView
        tabs={[
          {
            id: "properties",
            label: "Properties",
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/links/$linkId/properties",
              params,
            }),
          },
          {
            id: "time-series",
            label: t("global.timeSeries"),
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/links/$linkId/time-series",
              params,
            }),
          },
        ]}
      />
    </ViewWrapper>
  );
}
