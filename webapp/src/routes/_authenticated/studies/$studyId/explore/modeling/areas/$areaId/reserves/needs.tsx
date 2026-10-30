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
import { sortByName } from "@/services/utils";
import { buildKey } from "@/utils/reactUtils";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import useReserves from "./-hooks/useReserves";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/needs",
)({
  component: ReservesNeeds,
});

function reservesToOptions(reserves: Reserve[]) {
  return sortByName(reserves).map(({ id, name }) => ({ value: id, label: name }));
}

function ReservesNeeds() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const { studyId, areaId } = params;
  const { data: reserveOptions } = useReserves({ ...params, select: reservesToOptions });
  const { data: isReservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));
  const [selectedReserveId, setSelectedReserveId] = useState(() => reserveOptions[0]?.value ?? "");

  // Ensure the selected reserve ID is valid
  if (
    reserveOptions.length > 0 &&
    !reserveOptions.some(({ value }) => value === selectedReserveId)
  ) {
    setSelectedReserveId(reserveOptions[0].value);
  }

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<string>) => {
    setSelectedReserveId(event.target.value);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (reserveOptions.length === 0) {
    return <EmptyView icon={GridOffIcon} title={t("global.noData")} />;
  }

  return (
    <>
      <SelectFE
        label={t("study.modeling.reserves.needs.select")}
        value={selectedReserveId}
        options={reserveOptions}
        onChange={handleChange}
        size="extra-small"
        sx={{ minWidth: 200, maxWidth: 300 }}
      />
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <Matrix
          key={buildKey(params, selectedReserveId)}
          studyId={studyId}
          url={`input/reserves/${areaId}/${selectedReserveId}`}
          filterKey="reserves.needs"
          readOnly={!isReservesEnabled}
        />
      </Box>
    </>
  );
}
