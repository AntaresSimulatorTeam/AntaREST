/* eslint-disable camelcase */
import { useMemo } from "react";
import { MRT_ColumnDef } from "material-react-table";
import { Box, Chip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  ThermalClusterGroup,
  ThermalCluster,
  getThermalClusters,
  createThermalCluster,
  deleteThermalClusters,
  capacityAggregationFn,
  CLUSTER_GROUP_OPTIONS,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const currentAreaId = useAppSelector(getCurrentAreaId);
  const groups = Object.values(ThermalClusterGroup);

  const {
    data: clusters,
    isLoading,
    isRejected,
    isResolved,
    error,
  } = usePromiseWithSnackbarError(
    () => getThermalClusters(study.id, currentAreaId),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, currentAreaId],
    },
  );

  /**
   * Calculate the installed and enabled capacity for each thermal cluster.
   * - `installedCapacity` is calculated as the product of `unitCount` and `nominalCapacity`.
   * - `enabledCapacity` is the product of `unitCount` and `nominalCapacity` if the cluster is enabled, otherwise it's 0.
   * @function
   * @returns {Array} - An array of cluster objects, each augmented with `installedCapacity` and `enabledCapacity`.
   */
  const clustersWithCapacity = useMemo(
    () =>
      clusters?.map((cluster) => {
        const { unitCount, nominalCapacity, enabled } = cluster;
        const installedCapacity = unitCount * nominalCapacity;
        const enabledCapacity = enabled ? installedCapacity : 0;
        return { ...cluster, installedCapacity, enabledCapacity };
      }) || [],
    [clusters],
  );

  const { totalUnitCount, totalInstalledCapacity, totalEnabledCapacity } =
    useMemo(() => {
      if (!clusters) {
        return {
          totalUnitCount: 0,
          totalInstalledCapacity: 0,
          totalEnabledCapacity: 0,
        };
      }

      return clusters.reduce(
        (acc, { unitCount, nominalCapacity, enabled }) => {
          acc.totalUnitCount += unitCount;
          acc.totalInstalledCapacity += unitCount * nominalCapacity;
          acc.totalEnabledCapacity += enabled ? unitCount * nominalCapacity : 0;
          return acc;
        },
        {
          totalUnitCount: 0,
          totalInstalledCapacity: 0,
          totalEnabledCapacity: 0,
        },
      );
    }, [clusters]);

  const columns = useMemo<MRT_ColumnDef<ThermalCluster>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        size: 100,
        Cell: ({ renderedCellValue, row }) => {
          const clusterId = row.original.id;
          return (
            <Box
              sx={{
                cursor: "pointer",
                "&:hover": {
                  color: "primary.main",
                  textDecoration: "underline",
                },
              }}
              onClick={() => navigate(`${location.pathname}/${clusterId}`)}
            >
              {renderedCellValue}
            </Box>
          );
        },
      },
      {
        accessorKey: "group",
        header: "Group",
        size: 50,
        filterVariant: "select",
        filterSelectOptions: CLUSTER_GROUP_OPTIONS,
        muiTableHeadCellProps: {
          align: "left",
        },
        muiTableBodyCellProps: {
          align: "left",
        },
        Footer: () => (
          <Box sx={{ display: "flex", alignItems: "flex-start" }}>Total:</Box>
        ),
      },
      {
        accessorKey: "enabled",
        header: "Enabled",
        size: 50,
        filterVariant: "checkbox",
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue<boolean>() ? "Yes" : "No"}
            color={cell.getValue<boolean>() ? "success" : "error"}
            size="small"
          />
        ),
      },
      {
        accessorKey: "mustRun",
        header: "Must Run",
        size: 50,
        filterVariant: "checkbox",
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
        Footer: () => <Box color="warning.main">{totalUnitCount}</Box>,
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
        header: "Enabled / Installed",
        size: 50,
        aggregationFn: capacityAggregationFn,
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<string>() ?? ""} MW
          </Box>
        ),
        Cell: ({ row }) => (
          <>
            {row.original.enabledCapacity ?? 0} /{" "}
            {row.original.installedCapacity ?? 0} MW
          </>
        ),
        Footer: () => (
          <Box color="warning.main">
            {totalEnabledCapacity} / {totalInstalledCapacity} MW
          </Box>
        ),
      },
      {
        accessorKey: "marketBidCost",
        header: "Market Bid",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue<number>().toFixed(2)} €/MWh</>,
      },
    ],
    [
      location.pathname,
      navigate,
      totalEnabledCapacity,
      totalInstalledCapacity,
      totalUnitCount,
    ],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = ({
    id,
    installedCapacity,
    enabledCapacity,
    ...cluster
  }: ThermalCluster) => {
    return createThermalCluster(study.id, currentAreaId, cluster);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteThermalClusters(study.id, currentAreaId, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isLoading) {
    return <SimpleLoader />;
  }

  if (isRejected) {
    return <SimpleContent title={error?.toString()} />;
  }

  if (isResolved) {
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
}

export default Thermal;
