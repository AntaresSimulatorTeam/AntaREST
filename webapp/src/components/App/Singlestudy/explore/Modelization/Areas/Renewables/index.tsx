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
import { createMRTColumnHelper } from "material-react-table";
import { Box } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../types/types";
import {
  RENEWABLE_GROUPS,
  createRenewableCluster,
  deleteRenewableClusters,
  duplicateRenewableCluster,
  getRenewableClusters,
  type RenewableClusterWithCapacity,
  type RenewableGroup,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  addClusterCapacity,
  capacityAggregationFn,
  getClustersWithCapacityTotals,
  toCapacityString,
} from "../common/clustersUtils";
import type { TRow } from "../../../../../../common/GroupedDataTable/types";
import BooleanCell from "../../../../../../common/GroupedDataTable/cellRenderers/BooleanCell";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";

const columnHelper = createMRTColumnHelper<RenewableClusterWithCapacity>();

function Renewables() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);

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

  const handleCreate = async (values: TRow<RenewableGroup>) => {
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

  const handleNameClick = (row: RenewableClusterWithCapacity) => {
    navigate(`${location.pathname}/${row.id}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      isLoading={isLoading}
      data={clustersWithCapacity}
      columns={columns}
      groups={[...RENEWABLE_GROUPS]}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
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
