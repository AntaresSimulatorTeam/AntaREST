import { useMemo } from "react";
import { createMRTColumnHelper, type MRT_Row } from "material-react-table";
import { Box, Chip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  RENEWABLE_GROUPS,
  RenewableCluster,
  RenewableClusterWithCapacity,
  createRenewableCluster,
  deleteRenewableClusters,
  getRenewableClusters,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  capacityAggregationFn,
  useClusterDataWithCapacity,
} from "../common/utils";

function Renewables() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);
  const columnHelper = createMRTColumnHelper<RenewableClusterWithCapacity>();

  const {
    clustersWithCapacity,
    totalUnitCount,
    totalInstalledCapacity,
    totalEnabledCapacity,
    isLoading,
  } = useClusterDataWithCapacity<RenewableCluster>(
    () => getRenewableClusters(study.id, areaId),
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
      columnHelper.accessor("tsInterpretation", {
        header: "TS Interpretation",
        size: 50,
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
        Cell: ({ cell }) => Math.floor(cell.getValue()),
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
            {Math.floor(row.original.enabledCapacity ?? 0)} /{" "}
            {Math.floor(row.original.installedCapacity ?? 0)}
          </>
        ),
        Footer: () => (
          <Box color="warning.main">
            {totalEnabledCapacity} / {totalInstalledCapacity}
          </Box>
        ),
      }),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, totalEnabledCapacity, totalInstalledCapacity, totalUnitCount],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = ({
    id,
    installedCapacity,
    enabledCapacity,
    ...cluster
  }: RenewableClusterWithCapacity) => {
    return createRenewableCluster(study.id, areaId, cluster);
  };

  const handleDelete = (rows: RenewableClusterWithCapacity[]) => {
    const ids = rows.map((row) => row.id);
    return deleteRenewableClusters(study.id, areaId, ids);
  };

  const handleNameClick = (row: MRT_Row<RenewableClusterWithCapacity>) => {
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
      groups={RENEWABLE_GROUPS}
      onCreate={handleCreateRow}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
    />
  );
}

export default Renewables;
