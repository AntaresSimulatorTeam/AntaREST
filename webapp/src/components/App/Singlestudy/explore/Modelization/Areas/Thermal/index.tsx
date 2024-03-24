import { useMemo } from "react";
import { createMRTColumnHelper, type MRT_Row } from "material-react-table";
import { Box, Chip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  getThermalClusters,
  createThermalCluster,
  deleteThermalClusters,
  ThermalClusterWithCapacity,
  THERMAL_GROUPS,
  ThermalCluster,
  ThermalGroup,
  duplicateThermalCluster,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  addCapacity,
  capacityAggregationFn,
  useClusterDataWithCapacity,
} from "../common/utils";
import { TRow } from "../../../../../../common/GroupedDataTable/types";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);
  const columnHelper = createMRTColumnHelper<ThermalClusterWithCapacity>();

  const {
    clustersWithCapacity,
    totalUnitCount,
    totalInstalledCapacity,
    totalEnabledCapacity,
    isLoading,
  } = useClusterDataWithCapacity<ThermalCluster>(
    () => getThermalClusters(study.id, areaId),
    t("studies.error.retrieveData"),
    [study.id, areaId],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor("enabled", {
        header: "Enabled",
        size: 50,
        filterVariant: "checkbox",
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue() ? t("button.yes") : t("button.no")}
            color={cell.getValue() ? "success" : "error"}
            size="small"
            sx={{ minWidth: 40 }}
          />
        ),
      }),
      columnHelper.accessor("mustRun", {
        header: "Must Run",
        size: 50,
        filterVariant: "checkbox",
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue() ? t("button.yes") : t("button.no")}
            color={cell.getValue() ? "success" : "error"}
            size="small"
            sx={{ minWidth: 40 }}
          />
        ),
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
      columnHelper.accessor("installedCapacity", {
        header: "Enabled / Installed (MW)",
        size: 220,
        aggregationFn: capacityAggregationFn(),
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue() ?? ""}
          </Box>
        ),
        Cell: ({ row }) => (
          <>
            {Math.floor(row.original.enabledCapacity)} /{" "}
            {Math.floor(row.original.installedCapacity)}
          </>
        ),
        Footer: () => (
          <Box color="warning.main">
            {totalEnabledCapacity} / {totalInstalledCapacity}
          </Box>
        ),
      }),
      columnHelper.accessor("marketBidCost", {
        header: "Market Bid (€/MWh)",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue().toFixed(2)}</>,
      }),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, totalEnabledCapacity, totalInstalledCapacity, totalUnitCount],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TRow<ThermalGroup>) => {
    const cluster = await createThermalCluster(study.id, areaId, values);
    return addCapacity(cluster);
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

  const handleNameClick = (row: MRT_Row<ThermalClusterWithCapacity>) => {
    navigate(`${location.pathname}/${row.original.id}`);
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
    />
  );
}

export default Thermal;
