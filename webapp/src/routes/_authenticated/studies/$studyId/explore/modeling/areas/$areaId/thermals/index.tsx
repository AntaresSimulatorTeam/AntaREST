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

import DataTable from "@/components/DataTable";
import BooleanCell from "@/components/DataTable/cellRenderers/BooleanCell";
import type { RowData } from "@/components/DataTable/types";
import RefetchErrorAlert from "@/components/queries/RefetchErrorAlert";
import { thermalKeys } from "@/queries/thermals/keys";
import { thermalQueries } from "@/queries/thermals/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  capacityAggregationFn,
  selectClustersData,
  toCapacityString,
} from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-clustersUtils";
import { THERMAL_GROUPS } from "@/services/api/studies/areas/thermals/constants";
import { Box } from "@mui/material";
import { useIsMutating } from "@tanstack/react-query";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useCreateThermalCluster from "./-hooks/useCreateThermalCluster";
import useDeleteThermalClusters from "./-hooks/useDeleteThermalClusters";
import useDuplicateThermalCluster from "./-hooks/useDuplicateThermalCluster";
import useThermalClusters from "./-hooks/useThermalClusters";
import type { ThermalClusterWithCapacity } from "./-types";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(thermalQueries.list(studyId, areaId));
  },
  component: Thermals,
});

const columnHelper = createMRTColumnHelper<ThermalClusterWithCapacity>();

function Thermals() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();
  const createThermalCluster = useCreateThermalCluster(params);
  const duplicateThermalCluster = useDuplicateThermalCluster(params);
  const deleteThermalClusters = useDeleteThermalClusters(params);
  const { areaId } = params;

  const {
    data: { clustersWithCapacity, totals },
    error,
    isRefetchError,
  } = useThermalClusters({ ...params, select: selectClustersData });

  const isSaving =
    useIsMutating({
      mutationKey: thermalKeys.list(study.id, areaId),
    }) !== 0;

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

  const handleCreate = (values: RowData) => {
    createThermalCluster.mutate({ values });
  };

  const handleDuplicate = (row: ThermalClusterWithCapacity, newName: string) => {
    duplicateThermalCluster.mutate({ thermalId: row.id, newName });
  };

  const handleDelete = (rows: ThermalClusterWithCapacity[]) => {
    deleteThermalClusters.mutate({ thermalIds: rows.map((row) => row.id) });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <RefetchErrorAlert isRefetchError={isRefetchError} error={error} />
      <DataTable
        key={areaId}
        data={clustersWithCapacity}
        columns={columns}
        groups={[...THERMAL_GROUPS]}
        allowNewGroups={semver.gte(study.version, "9.3.0")}
        onCreate={handleCreate}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
        isSaving={isSaving}
        nameLinkOptions={(row) =>
          linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals/$thermalId",
            params: { ...params, thermalId: row.id },
          })
        }
        deleteConfirmationMessage={(rows) => {
          return t("study.modeling.clusters.question.delete", {
            count: rows.length,
            names: rows.map((row) => row.name),
          });
        }}
      />
    </>
  );
}
