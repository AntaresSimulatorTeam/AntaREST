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
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
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
  "/_authenticated/studies/$studyId/explore/modelization/areas/$areaId/storages/",
)({
  component: Storages,
});

const columnHelper = createMRTColumnHelper<FormalizedStorage>();

function Storages() {
  const study = useStudy();
  const area = useArea();
  const { t } = useTranslation();

  const { data: storages = [], isLoading } = usePromiseWithSnackbarError(
    () => getStorages(study.id, area.id),
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, area.id],
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
        header: t("study.modelization.storages.injectionNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modelization.storages.injectionNominalCapacity.info")}
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
        header: t("study.modelization.storages.withdrawalNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modelization.storages.withdrawalNominalCapacity.info")}
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
        header: t("study.modelization.storages.reservoirCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modelization.storages.reservoirCapacity.info")}
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
        header: t("study.modelization.storages.efficiency"),
        size: 50,
        Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevel", {
        header: t("study.modelization.storages.initialLevel"),
        size: 50,
        Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevelOptim", {
        header: t("study.modelization.storages.initialLevelOptim"),
        size: 200,
        filterVariant: "checkbox",
        Cell: BooleanCell,
      }),
      semver.gte(study.version, "9.2.0") &&
        columnHelper.accessor("efficiencyWithdrawal", {
          header: t("study.modelization.storages.efficiencyWithdrawal"),
          size: 50,
          Cell: ({ cell }) => `${Math.round(cell.getValue() * 100)}`,
        }),
    ].filter(Boolean);
  }, [study.version, t, totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = (values: TRow) => {
    return createStorage(study.id, area.id, values);
  };

  const handleDuplicate = (row: FormalizedStorage, newName: string) => {
    return duplicateStorage(study.id, area.id, row.id, newName);
  };

  const handleDelete = (rows: FormalizedStorage[]) => {
    const ids = rows.map((row) => row.id);
    return deleteStorages(study.id, area.id, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
          to: "/studies/$studyId/explore/modelization/areas/$areaId/storages/$storageId",
          params: {
            studyId: study.id,
            areaId: area.id,
            storageId: row.id,
          },
        })
      }
      deleteConfirmationMessage={(rows) => {
        return t("studies.modelization.clusters.question.delete", {
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
