/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import type { TRow } from "@/components/GroupedDataTable/types";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useStudy from "@/routes/-shared/hook/useStudy";
import { Box } from "@mui/material";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import {
  addClusterCapacity,
  capacityAggregationFn,
  getClustersWithCapacityTotals,
  toCapacityString,
} from "../../../../../../../../-App/Singlestudy/explore/Modelization/Areas/common/clustersUtils";
import {
  RENEWABLE_GROUPS,
  createRenewableCluster,
  deleteRenewableClusters,
  duplicateRenewableCluster,
  getRenewableClusters,
  type RenewableClusterWithCapacity,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/renewables/",
)({
  component: Renewables,
});

const columnHelper = createMRTColumnHelper<RenewableClusterWithCapacity>();

function Renewables() {
  const study = useStudy();
  const { areaId } = Route.useParams();
  const { t } = useTranslation();

  const { data: clustersWithCapacity = [], isLoading } = usePromiseWithSnackbarError<
    RenewableClusterWithCapacity[]
  >(
    async () => {
      const clusters = await getRenewableClusters(study.id, areaId);
      return clusters?.map(addClusterCapacity);
    },
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId],
    },
  );

  const [totals, setTotals] = useState(getClustersWithCapacityTotals(clustersWithCapacity));

  const columns = useMemo(() => {
    const { totalUnitCount, totalEnabledCapacity, totalInstalledCapacity } = totals;

    return [
      columnHelper.accessor("enabled", {
        header: "Enabled",
        size: 50,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      columnHelper.accessor("tsInterpretation", {
        header: "TS Interpretation",
        size: 50,
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
    ];
  }, [totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TRow) => {
    const cluster = await createRenewableCluster(study.id, areaId, values);
    return addClusterCapacity(cluster);
  };

  const handleDuplicate = async (row: RenewableClusterWithCapacity, newName: string) => {
    const cluster = await duplicateRenewableCluster(study.id, areaId, row.id, newName);

    return { ...row, ...cluster };
  };

  const handleDelete = (rows: RenewableClusterWithCapacity[]) => {
    const ids = rows.map((row) => row.id);
    return deleteRenewableClusters(study.id, areaId, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      isLoading={isLoading}
      data={clustersWithCapacity}
      columns={columns}
      groups={[...RENEWABLE_GROUPS] as string[]}
      allowNewGroups={semver.gte(study.version, "9.3.0")}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      nameLinkOptions={(row) =>
        linkOptions({
          to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId",
          params: {
            studyId: study.id,
            areaId,
            renewableId: row.id,
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

export default Renewables;
