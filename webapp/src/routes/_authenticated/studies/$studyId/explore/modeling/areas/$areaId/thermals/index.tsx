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
import { thermalKeys } from "@/queries/thermals/keys";
import { thermalQueries } from "@/queries/thermals/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  capacityAggregationFn,
  toCapacityString,
} from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-clustersUtils";
import { THERMAL_GROUPS } from "@/services/api/studies/areas/thermals/constants";
import { Box } from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useCreateThermal from "./-hooks/useCreateThermal";
import useDeleteThermals from "./-hooks/useDeleteThermals";
import useDuplicateThermal from "./-hooks/useDuplicateThermal";
import useThermals from "./-hooks/useThermals";
import { selectClustersData, type ThermalClusterWithCapacity } from "./-utils";

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
  const queryClient = useQueryClient();
  const createThermal = useCreateThermal(params);
  const duplicateThermal = useDuplicateThermal(params);
  const deleteThermals = useDeleteThermals(params);
  const { areaId } = params;

  const {
    data: { clustersWithCapacity, totals },
  } = useThermals({ ...params, select: selectClustersData });

  const isSaving = queryClient.isMutating({ mutationKey: thermalKeys.list(study.id, areaId) }) > 0;

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
    createThermal.mutate({ values });
  };

  const handleDuplicate = (row: ThermalClusterWithCapacity, newName: string) => {
    duplicateThermal.mutate({ thermalId: row.id, newName });
  };

  const handleDelete = (rows: ThermalClusterWithCapacity[]) => {
    deleteThermals.mutate({ thermalIds: rows.map((row) => row.id) });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
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
        return t("studies.modeling.clusters.question.delete", {
          count: rows.length,
          clusterNames: rows.map((row) => row.name),
        });
      }}
    />
  );
}
