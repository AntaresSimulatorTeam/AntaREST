/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";

import { Box } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import GroupedDataTable from "@/components/common/GroupedDataTable";
import BooleanCell from "@/components/common/GroupedDataTable/cellRenderers/BooleanCell";
import { TRow } from "@/components/common/GroupedDataTable/types";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentAreaId } from "@/redux/selectors";

import {
  addClusterCapacity,
  capacityAggregationFn,
  getClustersWithCapacityTotals,
  toCapacityString,
} from "../common/clustersUtils";

import {
  createThermalCluster,
  deleteThermalClusters,
  duplicateThermalCluster,
  getThermalClusters,
  THERMAL_GROUPS,
  type ThermalClusterWithCapacity,
  ThermalGroup,
} from "./utils";

const columnHelper = createMRTColumnHelper<ThermalClusterWithCapacity>();

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);

  const { data: clustersWithCapacity = [], isLoading } =
    usePromiseWithSnackbarError<ThermalClusterWithCapacity[]>(
      async () => {
        const clusters = await getThermalClusters(study.id, areaId);
        return clusters?.map(addClusterCapacity);
      },
      {
        resetDataOnReload: true,
        errorMessage: t("studies.error.retrieveData"),
        deps: [study.id, areaId],
      },
    );

  const [totals, setTotals] = useState(
    getClustersWithCapacityTotals(clustersWithCapacity),
  );

  const columns = useMemo(() => {
    const { totalUnitCount, totalEnabledCapacity, totalInstalledCapacity } =
      totals;

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
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue()}
          </Box>
        ),
        Footer: () => <Box color="warning.main">{totalUnitCount}</Box>,
      }),
      columnHelper.accessor("nominalCapacity", {
        header: "Nominal Capacity (MW)",
        size: 220,
        Cell: ({ cell }) => cell.getValue().toFixed(1),
      }),
      columnHelper.accessor(
        (row) => toCapacityString(row.enabledCapacity, row.installedCapacity),
        {
          header: "Enabled / Installed (MW)",
          size: 220,
          aggregationFn: capacityAggregationFn(),
          AggregatedCell: ({ cell }) => (
            <Box sx={{ color: "info.main", fontWeight: "bold" }}>
              {cell.getValue()}
            </Box>
          ),
          Footer: () => (
            <Box color="warning.main">
              {toCapacityString(totalEnabledCapacity, totalInstalledCapacity)}
            </Box>
          ),
        },
      ),
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

  const handleCreate = async (values: TRow<ThermalGroup>) => {
    const cluster = await createThermalCluster(study.id, areaId, values);
    return addClusterCapacity(cluster);
  };

  const handleDuplicate = async (
    row: ThermalClusterWithCapacity,
    newName: string,
  ) => {
    const cluster = await duplicateThermalCluster(
      study.id,
      areaId,
      row.id,
      newName,
    );

    return { ...row, ...cluster };
  };

  const handleDelete = (rows: ThermalClusterWithCapacity[]) => {
    const ids = rows.map((row) => row.id);
    return deleteThermalClusters(study.id, areaId, ids);
  };

  const handleNameClick = (row: ThermalClusterWithCapacity) => {
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
      groups={[...THERMAL_GROUPS]}
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

export default Thermal;
