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
import { reserveQueries } from "@/queries/reserves/queries";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves",
)({
  loader: async ({ context, params: { studyId } }) => {
    await context.queryClient.ensureQueryData(reserveQueries.includeReserves(studyId));
  },
  component: ReservesLayout,
});

function ReservesLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();

  return (
    <TabsView
      tabs={[
        {
          id: "general",
          label: t("global.general"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/reserves/general",
            params,
          }),
        },
        {
          id: "needs",
          label: t("study.modeling.reserves.needs"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/reserves/needs",
            params,
          }),
        },
      ]}
    />
  );
}
