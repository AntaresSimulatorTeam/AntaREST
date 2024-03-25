import { useMemo } from "react";
import { createMRTColumnHelper, type MRT_Row } from "material-react-table";
import { Box } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  RENEWABLE_GROUPS,
  RenewableCluster,
  RenewableClusterWithCapacity,
  RenewableGroup,
  createRenewableCluster,
  deleteRenewableClusters,
  duplicateRenewableCluster,
  getRenewableClusters,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  addCapacity,
  capacityAggregationFn,
  useClusterDataWithCapacity,
} from "../common/clustersUtils";
import { TRow } from "../../../../../../common/GroupedDataTable/types";
import BooleanCell from "../../../../../../common/GroupedDataTable/cellRenderers/BooleanCell";

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
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, totalEnabledCapacity, totalInstalledCapacity, totalUnitCount],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TRow<RenewableGroup>) => {
    const cluster = await createRenewableCluster(study.id, areaId, values);
    return addCapacity(cluster);
  };

  const handleDuplicate = async (
    row: RenewableClusterWithCapacity,
    newName: string,
  ) => {
    const cluster = await duplicateRenewableCluster(
      study.id,
      areaId,
      row.id,
      newName,
    );

    return { ...row, ...cluster };
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
      groups={[...RENEWABLE_GROUPS]}
      onCreate={handleCreate}
      onDuplicate={handleDuplicate}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
      fillPendingRow={(row) => ({
        ...row,
        enabledCapacity: 0,
        installedCapacity: 0,
      })}
    />
  );
}

export default Renewables;
