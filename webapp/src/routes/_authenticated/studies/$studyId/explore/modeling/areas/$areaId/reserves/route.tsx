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
import { Alert, Stack } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, linkOptions, Outlet } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(reserveQueries.list(studyId, areaId));
    await context.queryClient.ensureQueryData(reserveQueries.enabled(studyId));
  },
  component: ReservesLayout,
});

function ReservesLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const { studyId } = params;
  const { data: isReservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));

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
        {
          id: "certifications",
          label: t("study.modeling.reserves.certifications"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/reserves/certifications",
            params,
          }),
        },
        {
          id: "symmetries",
          label: t("study.modeling.reserves.symmetries"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/reserves/symmetries",
            params,
          }),
        },
      ]}
      renderOutlet={() => (
        <Stack direction="column" spacing={1} sx={{ height: 1 }}>
          {!isReservesEnabled && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              {t("study.modeling.reserves.readOnly.alert")}
            </Alert>
          )}
          <Outlet />
        </Stack>
      )}
    />
  );
}
