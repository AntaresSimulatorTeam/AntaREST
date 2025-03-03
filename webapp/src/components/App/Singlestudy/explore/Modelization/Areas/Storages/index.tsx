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

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { createMRTColumnHelper } from "material-react-table";
import { Box, Tooltip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import type { StudyMetadata } from "../../../../../../../types/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  getStorages,
  deleteStorages,
  createStorage,
  STORAGE_GROUPS,
  duplicateStorage,
  getStoragesTotals,
  type Storage,
  type StorageGroup,
} from "./utils";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import type { TRow } from "../../../../../../common/GroupedDataTable/types";
import BooleanCell from "../../../../../../common/GroupedDataTable/cellRenderers/BooleanCell";

const columnHelper = createMRTColumnHelper<Storage>();

function Storages() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);
  const studyVersion = parseInt(study.version, 10);

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
      studyVersion >= 880 &&
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
    ].filter(Boolean);
  }, [studyVersion, t, totals]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = (values: TRow<StorageGroup>) => {
    return createStorage(study.id, areaId, values);
  };

  const handleDuplicate = (row: Storage, newName: string) => {
    return duplicateStorage(study.id, areaId, row.id, newName);
  };

  const handleDelete = (rows: Storage[]) => {
    const ids = rows.map((row) => row.id);
    return deleteStorages(study.id, areaId, ids);
  };

  const handleNameClick = (row: Storage) => {
    navigate(`${location.pathname}/${row.id}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      isLoading={isLoading}
      data={storages || []}
      columns={columns}
      groups={[...STORAGE_GROUPS]}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
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

export default Storages;
