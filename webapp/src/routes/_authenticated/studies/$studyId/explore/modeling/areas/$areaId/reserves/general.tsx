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
import EmptyView from "@/components/page/EmptyView";
import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import { Chip } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/general",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(reserveQueries.list(studyId, areaId));
  },
  component: ReservesGeneral,
});

interface ReserveRow extends Reserve {
  name: string;
}

function reservesToRows(reserves: Reserve[]): ReserveRow[] {
  return reserves.map((reserve) => ({ ...reserve, name: reserve.id }));
}

const columnHelper = createMRTColumnHelper<ReserveRow>();

const columns = [
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
];

function ReservesGeneral() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();

  const { data: rows } = useSuspenseQuery({
    ...reserveQueries.list(studyId, areaId),
    select: reservesToRows,
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (rows.length === 0) {
    return <EmptyView title={t("study.modeling.reserves.empty")} />;
  }

  return <GroupedDataTable data={rows} columns={columns} />;
}
