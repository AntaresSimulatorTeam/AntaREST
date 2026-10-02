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
import BooleanCell from "@/components/GroupedDataTable/cellRenderers/BooleanCell";
import type { RowData } from "@/components/GroupedDataTable/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  addClusterCapacity,
  capacityAggregationFn,
  getClustersWithCapacityTotals,
  toCapacityString,
} from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-clustersUtils";
import { Box } from "@mui/material";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { adaptThermalClusterToView } from "./-adapters";
import useCreateThermalCluster from "./-hooks/useCreateThermalCluster";
import useDeleteThermalClusters from "./-hooks/useDeleteThermalClusters";
import useDuplicateThermalCluster from "./-hooks/useDuplicateThermalCluster";
import useThermalClusters from "./-hooks/useThermalClusters";
import { THERMAL_GROUPS, type ThermalClusterWithCapacity } from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/",
)({
  component: Thermals,
});

const columnHelper = createMRTColumnHelper<ThermalClusterWithCapacity>();

function Thermals() {
  const study = useStudy();
  const { areaId } = Route.useParams();
  const { t } = useTranslation();

  const scope = { studyId: study.id, areaId };
  const { data: clusters, isPending, status, error } = useThermalClusters(scope);
  const createCluster = useCreateThermalCluster(scope);
  const duplicateCluster = useDuplicateThermalCluster(scope);
  const deleteClusters = useDeleteThermalClusters(scope);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const clustersWithCapacity = useMemo(() => clusters?.map(addClusterCapacity) ?? [], [clusters]);

  useEffect(() => {
    if (error) {
      enqueueErrorSnackbar(t("studies.error.retrieveData"), error);
    }
  }, [enqueueErrorSnackbar, t, error]);

  const [totals, setTotals] = useState(() => getClustersWithCapacityTotals(clustersWithCapacity));

  const columns = useMemo(() => {
    const { totalUnitCount, totalEnabledCapacity, totalInstalledCapacity } = totals;

    return [
      columnHelper.accessor("enabled", {
        header: "Enabled",
        size: 50,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      columnHelper.accessor("mustRun", {
        header: "Must Run",
        size: 50,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      columnHelper.accessor("unitCount", {
        header: "Unit Count",
        size: 50,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>{cell.getValue()}</Box>
        ),
        Footer: () => <Box color="warning.main">{totalUnitCount}</Box>,
      }),
      columnHelper.accessor("nominalCapacity", {
        header: "Nominal Capacity (MW)",
        size: 220,
        Cell: ({ cell }) => cell.getValue().toFixed(1),
      }),
      columnHelper.accessor((row) => toCapacityString(row.enabledCapacity, row.installedCapacity), {
        header: "Enabled / Installed (MW)",
        size: 220,
        aggregationFn: capacityAggregationFn(),
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>{cell.getValue()}</Box>
        ),
        Footer: () => (
          <Box color="warning.main">
            {toCapacityString(totalEnabledCapacity, totalInstalledCapacity)}
          </Box>
        ),
      }),
      columnHelper.accessor("marketBidCost", {
        header: "Market Bid (€/MWh)",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue().toFixed(2)}</>,
      }),
    ];
  }, [totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: RowData) => {
    const cluster = await createCluster.mutateAsync({ ...scope, values });
    return addClusterCapacity(adaptThermalClusterToView(cluster));
  };

  const handleDuplicate = async (row: ThermalClusterWithCapacity, newName: string) => {
    const cluster = await duplicateCluster.mutateAsync({ ...scope, clusterId: row.id, newName });
    return addClusterCapacity(adaptThermalClusterToView(cluster));
  };

  const handleDelete = (rows: ThermalClusterWithCapacity[]) => {
    const ids = rows.map((row) => row.id);
    return deleteClusters.mutateAsync({ ...scope, clusterIds: ids });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      key={`${study.id}/${areaId}/${clusters ? "loaded" : status}`}
      isLoading={isPending}
      readOnly={!clusters}
      data={clustersWithCapacity}
      columns={columns}
      groups={[...THERMAL_GROUPS] as string[]}
      allowNewGroups={semver.gte(study.version, "9.3.0")}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      nameLinkOptions={(row) =>
        linkOptions({
          to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId",
          params: {
            studyId: study.id,
            areaId,
            thermalId: row.id,
          },
        })
      }
      deleteConfirmationMessage={(rows) => {
        return t("studies.modeling.clusters.question.delete", {
          count: rows.length,
          clusterNames: rows.map((row) => row.name),
        });
      }}
      fillPendingRow={(row) => ({
        unitCount: 0,
        enabledCapacity: 0,
        installedCapacity: 0,
        ...row,
      })}
      onDataChange={(data) => {
        setTotals(getClustersWithCapacityTotals(data));
      }}
    />
  );
}
