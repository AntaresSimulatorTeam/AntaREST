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
import { storageKeys } from "@/queries/storages/keys";
import { storageQueries } from "@/queries/storages/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { STORAGE_GROUPS } from "@/services/api/studies/areas/storages/constants";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { Box, Tooltip } from "@mui/material";
import { useIsMutating } from "@tanstack/react-query";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useCreateStorage from "./-hooks/useCreateStorage";
import useDeleteStorages from "./-hooks/useDeleteStorages";
import useDuplicateStorage from "./-hooks/useDuplicateStorage";
import useStorages from "./-hooks/useStorages";
import type { FormalizedStorage } from "./-types";
import { selectStoragesData } from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(storageQueries.list(studyId, areaId));
  },
  component: Storages,
});

const columnHelper = createMRTColumnHelper<FormalizedStorage>();

function Storages() {
  const study = useStudy();
  const params = Route.useParams();
  const { t } = useTranslation();
  const createStorage = useCreateStorage(params);
  const duplicateStorage = useDuplicateStorage(params);
  const deleteStorages = useDeleteStorages(params);
  const { areaId } = params;

  const {
    data: { formalizedStorages, totals },
    error,
    isRefetchError,
  } = useStorages({ ...params, select: selectStoragesData });

  const isSaving =
    useIsMutating({
      mutationKey: storageKeys.list(study.id, areaId),
    }) !== 0;

  const columns = useMemo(() => {
    const { totalInjectionNominalCapacity, totalWithdrawalNominalCapacity } = totals;

    return [
      semver.gte(study.version, "8.8.0") &&
        columnHelper.accessor("enabled", {
          header: t("global.enabled"),
          Cell: BooleanCell,
        }),
      columnHelper.accessor("injectionNominalCapacity", {
        header: t("study.modeling.storages.injectionNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modeling.storages.injectionNominalCapacity.info")}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>{Math.round(cell.getValue())}</Box>
        ),
        Cell: ({ cell }) => Math.round(cell.getValue()),
        Footer: () => <Box color="warning.main">{Math.round(totalInjectionNominalCapacity)}</Box>,
      }),
      columnHelper.accessor("withdrawalNominalCapacity", {
        header: t("study.modeling.storages.withdrawalNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modeling.storages.withdrawalNominalCapacity.info")}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>{Math.round(cell.getValue())}</Box>
        ),
        Cell: ({ cell }) => Math.round(cell.getValue()),
        Footer: () => <Box color="warning.main">{Math.round(totalWithdrawalNominalCapacity)}</Box>,
      }),
      columnHelper.accessor("reservoirCapacity", {
        header: t("study.modeling.storages.reservoirCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modeling.storages.reservoirCapacity.info")}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        Cell: ({ cell }) => `${cell.getValue()}`,
      }),
      columnHelper.accessor("efficiency", {
        header: t("study.modeling.storages.efficiency"),
        Header: ({ column }) => (
          <Tooltip title={t("study.modeling.storages.efficiency.info")} placement="top" arrow>
            <span>{column.columnDef.header}</span>
          </Tooltip>
        ),
        size: 50,
        Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevel", {
        header: t("study.modeling.storages.initialLevel"),
        size: 50,
        Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevelOptim", {
        header: t("study.modeling.storages.initialLevelOptim"),
        size: 200,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      semver.gte(study.version, "9.2.0") &&
        columnHelper.accessor("efficiencyWithdrawal", {
          header: t("study.modeling.storages.efficiencyWithdrawal"),
          size: 50,
          Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
        }),
    ].filter(Boolean);
  }, [study.version, t, totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = (values: RowData) => {
    createStorage.mutate({ values });
  };

  const handleDuplicate = (row: FormalizedStorage, newName: string) => {
    duplicateStorage.mutate({ storageId: row.id, newName });
  };

  const handleDelete = (rows: FormalizedStorage[]) => {
    deleteStorages.mutate({ storageIds: rows.map((row) => row.id) });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  checkRouteAvailability({
    studyVersion: study.version,
    minVersion: "8.6.0",
    routePath: Route.path,
  });

  return (
    <>
      <RefetchErrorAlert isRefetchError={isRefetchError} error={error} />
      <DataTable
        key={areaId}
        data={formalizedStorages}
        columns={columns}
        groups={[...STORAGE_GROUPS]}
        allowNewGroups={semver.gte(study.version, "9.2.0")}
        onCreate={handleCreate}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
        isSaving={isSaving}
        nameLinkOptions={(row) =>
          linkOptions({
            to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
            params: { ...params, storageId: row.id },
          })
        }
        deleteConfirmationMessage={(rows) => {
          return t("studies.modeling.clusters.question.delete", {
            count: rows.length,
            names: rows.map((row) => row.name),
          });
        }}
      />
    </>
  );
}
