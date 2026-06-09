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

import GroupedDataTable from "@/components/GroupedDataTable";
import TabsView from "@/components/page/TabsView";
import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import { Chip } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves",
)({
  loader: ({ context, params: { studyId, areaId } }) => {
    return context.queryClient.ensureQueryData(reserveQueries.list(studyId, areaId));
  },
  component: Reserves,
});

interface ReserveRow extends Reserve {
  name: string;
}

const columnHelper = createMRTColumnHelper<ReserveRow>();

function Reserves() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();

  const { data: reserves } = useSuspenseQuery(reserveQueries.list(studyId, areaId));

  const rows = useMemo<ReserveRow[]>(
    () => reserves.map((reserve) => ({ ...reserve, name: reserve.id })),
    [reserves],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor("type", {
        header: "Type",
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue()}
            size="small"
            color={cell.getValue() === "up" ? "success" : "warning"}
            variant="outlined"
            sx={{ borderRadius: 1, textTransform: "uppercase" }}
          />
        ),
      }),
      columnHelper.accessor("failureCost", { header: "Failure Cost" }),
      columnHelper.accessor("spillageCost", { header: "Spillage Cost" }),
      columnHelper.accessor("referenceActivationDuration", {
        header: "Ref. Activation Duration",
      }),
      columnHelper.accessor("powerActivationRatio", { header: "Power Activation Ratio" }),
      columnHelper.accessor("energyActivationRatio", { header: "Energy Activation Ratio" }),
    ],
    [],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabsView
      tabs={[
        {
          id: "general",
          label: t("global.general"),
          content: <GroupedDataTable data={rows} columns={columns} />,
        },
      ]}
    />
  );
}
