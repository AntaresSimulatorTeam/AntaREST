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

import DataGridSkeleton from "@/components/DataGridSkeleton";
import ThermalClusterListGrid, {
  type ThermalClusterRow,
} from "@/components/DataGrid/examples/ThermalClusterListGrid";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { createFileRoute } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { getThermalClusters, updateThermalCluster, type ThermalCluster } from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/",
)({
  component: Thermals,
});

////////////////////////////////////////////////////////////////
// Mapping
////////////////////////////////////////////////////////////////

function toRow(cluster: ThermalCluster): ThermalClusterRow {
  return {
    id: cluster.id,
    name: cluster.name,
    group: cluster.group,
    enabled: cluster.enabled,
    mustRun: cluster.mustRun,
    unitCount: cluster.unitCount,
    nominalCapacity: cluster.nominalCapacity,
    marketBidCost: cluster.marketBidCost,
    genTs: cluster.genTs,
  };
}

////////////////////////////////////////////////////////////////
// Component
////////////////////////////////////////////////////////////////

function Thermals() {
  const study = useStudy();
  const { areaId } = Route.useParams();
  const { t } = useTranslation();

  const {
    data: clusters = [],
    isLoading,
    status,
  } = usePromiseWithSnackbarError(
    async () => {
      const list = await getThermalClusters(study.id, areaId);
      return list.map(toRow);
    },
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSaveRow = useCallback(
    async (id: string, changes: Partial<ThermalClusterRow>) => {
      await updateThermalCluster(study.id, areaId, id, changes as Partial<ThermalCluster>);
    },
    [study.id, areaId],
  );

  const handleSaveAll = useCallback(
    async (rows: ThermalClusterRow[]) => {
      await Promise.all(
        rows.map((row) =>
          updateThermalCluster(study.id, areaId, row.id, row as Partial<ThermalCluster>),
        ),
      );
    },
    [study.id, areaId],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isLoading) {
    return <DataGridSkeleton />;
  }

  return (
    <ThermalClusterListGrid
      key={status}
      clusters={clusters}
      onSaveRow={handleSaveRow}
      onSaveAll={handleSaveAll}
    />
  );
}
