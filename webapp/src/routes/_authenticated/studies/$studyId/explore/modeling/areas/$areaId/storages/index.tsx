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
import type { TRow } from "@/components/GroupedDataTable/types";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { checkRouteAvailability } from "@/utils/routerUtils";
import { Box, Tooltip } from "@mui/material";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import usePromiseWithSnackbarError from "../../../../../../../../../hooks/usePromiseWithSnackbarError";
import {
  createStorage,
  deleteStorages,
  duplicateStorage,
  getStorages,
  getStoragesTotals,
  STORAGE_GROUPS,
  type FormalizedStorage,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/",
)({
  component: Storages,
});

const columnHelper = createMRTColumnHelper<FormalizedStorage>();

function Storages() {
  const study = useStudy();
  const { areaId } = Route.useParams();
  const { t } = useTranslation();

  const { data: storages = [], isLoading } = usePromiseWithSnackbarError(
    () => getStorages(study.id, areaId),
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId],
    },
  );

  const [totals, setTotals] = useState(getStoragesTotals(storages));

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

  const handleCreate = (values: TRow) => {
    return createStorage(study.id, areaId, values);
  };

  const handleDuplicate = (row: FormalizedStorage, newName: string) => {
    return duplicateStorage(study.id, areaId, row.id, newName);
  };

  const handleDelete = (rows: FormalizedStorage[]) => {
    const ids = rows.map((row) => row.id);
    return deleteStorages(study.id, areaId, ids);
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
    <GroupedDataTable
      isLoading={isLoading}
      data={storages || []}
      columns={columns}
      groups={[...STORAGE_GROUPS] as string[]}
      allowNewGroups={semver.gte(study.version, "9.2.0")}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      nameLinkOptions={(row) =>
        linkOptions({
          to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
          params: {
            studyId: study.id,
            areaId,
            storageId: row.id,
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
        withdrawalNominalCapacity: 0,
        injectionNominalCapacity: 0,
        ...row,
      })}
      onDataChange={(data) => {
        setTotals(getStoragesTotals(data));
      }}
    />
  );
}
