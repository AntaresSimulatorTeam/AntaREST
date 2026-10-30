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
import type { MainRowData } from "@/components/DataTable/types";
import RefetchErrorAlert from "@/components/queries/RefetchErrorAlert";
import { renewableKeys } from "@/queries/renewables/keys";
import { renewableQueries } from "@/queries/renewables/queries";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudySynthesis } from "@/redux/selectors";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { RENEWABLE_GROUPS } from "@/services/api/studies/areas/renewables/constants";
import { Box } from "@mui/material";
import { useIsMutating } from "@tanstack/react-query";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { capacityAggregationFn, selectClustersData, toCapacityString } from "../-clustersUtils";
import useCreateRenewableCluster from "./-hooks/useCreateRenewableCluster";
import useDeleteRenewableClusters from "./-hooks/useDeleteRenewableClusters";
import useDuplicateRenewableCluster from "./-hooks/useDuplicateRenewableCluster";
import useRenewableClusters from "./-hooks/useRenewableClusters";
import type { RenewableClusterWithCapacity } from "./-types";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/renewables/",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(renewableQueries.list(studyId, areaId));
  },
  component: Renewables,
});

const columnHelper = createMRTColumnHelper<RenewableClusterWithCapacity>();

function Renewables() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();
  const createRenewableCluster = useCreateRenewableCluster(params);
  const duplicateRenewableCluster = useDuplicateRenewableCluster(params);
  const deleteRenewableClusters = useDeleteRenewableClusters(params);
  const enrModelling = useAppSelector((state) => getStudySynthesis(state, study.id)?.enr_modelling);
  const { areaId } = params;

  const {
    data: { clustersWithCapacity, totals },
    error,
    isRefetchError,
  } = useRenewableClusters({ ...params, select: selectClustersData });

  const isSaving =
    useIsMutating({
      mutationKey: renewableKeys.list(study.id, areaId),
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

  const handleCreate = (values: MainRowData) => {
    createRenewableCluster.mutate({ values });
  };

  const handleDuplicate = (row: RenewableClusterWithCapacity, newName: string) => {
    duplicateRenewableCluster.mutate({ renewableId: row.id, newName });
  };

  const handleDelete = (rows: RenewableClusterWithCapacity[]) => {
    deleteRenewableClusters.mutate({ renewableIds: rows.map((row) => row.id) });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (enrModelling !== "clusters") {
    throw new Error(`${Route.path} is only available when 'enr_modelling' is of type clusters.`);
  }

  return (
    <>
      <RefetchErrorAlert isRefetchError={isRefetchError} error={error} />
      <DataTable
        key={areaId}
        data={clustersWithCapacity}
        columns={columns}
        groups={[...RENEWABLE_GROUPS]}
        allowNewGroups={semver.gte(study.version, "9.3.0")}
        onCreate={handleCreate}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
        isSaving={isSaving}
        nameLinkOptions={(row) =>
          linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId",
            params: { ...params, renewableId: row.id },
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
