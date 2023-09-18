/* eslint-disable camelcase */
import { useMemo } from "react";
import { MRT_ColumnDef } from "material-react-table";
import { Box, Chip, Stack } from "@mui/material";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  ThermalClusterGroup,
  ThermalCluster,
  getThermalClusters,
  createThermalCluster,
  deleteThermalClusters,
  capacityAggregationFn,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import usePromise from "../../../../../../../hooks/usePromise";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const groups = Object.values(ThermalClusterGroup);

  const { data: clusters } = usePromise(
    () => getThermalClusters(study.id, currentArea),
    [study.id, currentArea]
  );

  /**
   * Calculates the installed and enabled capacity for each thermal cluster.
   * @installedCapacity = unitCount * nominalCapacity.
   * @enabledCapacity = unitCount * nominalCapacity if enabled is true else = 0.
   */
  const clustersWithCapacity = useMemo(
    () =>
      clusters?.map((cluster) => {
        const { unitCount, nominalCapacity, enabled } = cluster;
        const installedCapacity = unitCount * nominalCapacity;
        const enabledCapacity = enabled ? installedCapacity : 0;
        return { ...cluster, installedCapacity, enabledCapacity };
      }) || [],
    [clusters]
  );

  const totalUnitCount = useMemo(
    () => clusters?.reduce((acc, curr) => acc + curr.unitCount, 0),
    [clusters]
  );

  const totalInstalledCapacity = useMemo(
    () =>
      clusters?.reduce(
        (acc, curr) => acc + curr.unitCount * curr.nominalCapacity,
        0
      ),
    [clusters]
  );

  const totalEnabledCapacity = useMemo(
    () =>
      clusters?.reduce(
        (acc, curr) =>
          acc + (curr.enabled ? curr.unitCount * curr.nominalCapacity : 0),
        0
      ),
    [clusters]
  );

  const columns = useMemo<MRT_ColumnDef<ThermalCluster>[]>(
    () => [
      {
        accessorKey: "group",
        header: "Group",
        size: 50,
        muiTableHeadCellProps: {
          align: "left",
        },
        muiTableBodyCellProps: {
          align: "left",
        },
      },
      {
        accessorKey: "enabled",
        header: "Enabled",
        size: 50,
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue<boolean>() ? "Yes" : "No"}
            color={cell.getValue<boolean>() ? "success" : "error"}
            size="small"
          />
        ),
      },
      {
        accessorKey: "unitCount",
        header: "Unit Count",
        size: 50,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<number>()}
          </Box>
        ),
        Footer: () => (
          <Stack>
            Total Units:
            <Box color="warning.main">{totalUnitCount}</Box>
          </Stack>
        ),
      },
      {
        accessorKey: "nominalCapacity",
        header: "Nominal Capacity",
        size: 50,
        aggregationFn: "sum",
        Cell: ({ cell }) => <>{cell.getValue<number>()} MW</>,
      },
      {
        accessorKey: "installedCapacity",
        header: "Installed Capacity",
        size: 50,
        aggregationFn: capacityAggregationFn,
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<string>() ?? ""} MW
          </Box>
        ),
        Cell: ({ row }) => (
          <>
            {row.original.enabledCapacity ?? 0}/
            {row.original.installedCapacity ?? 0} MW
          </>
        ),
        Footer: () => (
          <Stack>
            Total Installed:
            <Box color="warning.main">
              {totalEnabledCapacity}/{totalInstalledCapacity} MW
            </Box>
          </Stack>
        ),
      },
      {
        accessorKey: "marketBidCost",
        header: "Market Bid",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue<number>().toFixed(2)} €/MWh</>,
      },
    ],
    [totalEnabledCapacity, totalInstalledCapacity, totalUnitCount]
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = ({ name, group }: ThermalCluster) => {
    return createThermalCluster(study.id, currentArea, {
      name,
      group,
    });
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteThermalClusters(study.id, currentArea, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!clusters) {
    return <SimpleLoader />;
  }

  return (
    <GroupedDataTable
      data={clustersWithCapacity}
      columns={columns}
      groups={groups}
      onCreate={handleCreateRow}
      onDelete={handleDeleteSelection}
    />
  );
}

export default Thermal;
