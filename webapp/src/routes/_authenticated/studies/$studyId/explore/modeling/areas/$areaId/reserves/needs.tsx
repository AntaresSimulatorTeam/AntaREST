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

import Matrix from "@/components/Matrix";
import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import EmptyView from "@/components/page/EmptyView";
import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/needs",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(reserveQueries.list(studyId, areaId));
  },
  component: ReservesNeeds,
});

function reserveToOption(reserve: Reserve) {
  return { label: reserve.id, value: reserve.id };
}

function ReservesNeeds() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();

  const { data: reserves } = useSuspenseQuery(reserveQueries.list(studyId, areaId));

  const [selectedReserveId, setSelectedReserveId] = useState(() => reserves[0]?.id ?? "");

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<string>) => {
    setSelectedReserveId(event.target.value);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (reserves.length === 0) {
    return <EmptyView icon={GridOffIcon} title={t("study.modeling.reserves.needs.empty")} />;
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: 1, gap: 1 }}>
      <SelectFE
        label={t("study.modeling.reserves.needs.select")}
        value={selectedReserveId}
        options={reserves.map(reserveToOption)}
        onChange={handleChange}
        size="extra-small"
        sx={{ minWidth: 200, maxWidth: 300 }}
      />
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <Matrix
          key={`${areaId}-${selectedReserveId}`}
          studyId={studyId}
          url={`input/reserves/${areaId}/${selectedReserveId}`}
        />
      </Box>
    </Box>
  );
}
