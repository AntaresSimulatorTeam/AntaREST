/* eslint-disable camelcase */
import { useMemo } from "react";
import { MRT_ColumnDef } from "material-react-table";
import { Box, Chip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../common/types";
import {
  getThermalClusters,
  createThermalCluster,
  deleteThermalClusters,
  capacityAggregationFn,
  ThermalClusterWithCapacity,
  THERMAL_GROUPS,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const currentAreaId = useAppSelector(getCurrentAreaId);

  const clusters = usePromiseWithSnackbarError(
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
   * @returns {Array} - An array of cluster objects, each augmented with `installedCapacity` and `enabledCapacity`.
   */
  const clustersWithCapacity = useMemo(
    () =>
      clusters?.data?.map((cluster) => {
        const { unitCount, nominalCapacity, enabled } = cluster;
        const installedCapacity = unitCount * nominalCapacity;
        const enabledCapacity = enabled ? installedCapacity : 0;
        return { ...cluster, installedCapacity, enabledCapacity };
      }) || [],
    [clusters],
  );

  const { totalUnitCount, totalInstalledCapacity, totalEnabledCapacity } =
    useMemo(() => {
      if (!clustersWithCapacity) {
        return {
          totalUnitCount: 0,
          totalInstalledCapacity: 0,
          totalEnabledCapacity: 0,
        };
      }

      return clustersWithCapacity.reduce(
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
    }, [clustersWithCapacity]);

  const columns = useMemo<MRT_ColumnDef<ThermalClusterWithCapacity>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        size: 100,
        muiTableHeadCellProps: {
          align: "left",
        },
        muiTableBodyCellProps: {
          align: "left",
        },
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
        filterSelectOptions: [...THERMAL_GROUPS],
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
        header: "Nominal Capacity (MW)",
        size: 200,
        aggregationFn: "sum",
        Cell: ({ cell }) => <>{cell.getValue<number>()}</>,
      },
      {
        accessorKey: "installedCapacity",
        header: "Enabled / Installed (MW)",
        size: 200,
        aggregationFn: capacityAggregationFn,
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<string>() ?? ""}
          </Box>
        ),
        Cell: ({ row }) => (
          <>
            {row.original.enabledCapacity ?? 0} /{" "}
            {row.original.installedCapacity ?? 0}
          </>
        ),
        Footer: () => (
          <Box color="warning.main">
            {totalEnabledCapacity} / {totalInstalledCapacity}
          </Box>
        ),
      },
      {
        accessorKey: "marketBidCost",
        header: "Market Bid (€/MWh)",
        size: 50,
        Cell: ({ cell }) => <>{cell.getValue<number>().toFixed(2)}</>,
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
  }: ThermalClusterWithCapacity) => {
    return createThermalCluster(study.id, currentAreaId, cluster);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteThermalClusters(study.id, currentAreaId, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={clusters}
      ifPending={() => <SimpleLoader />}
      ifResolved={() => (
        <GroupedDataTable
          data={clustersWithCapacity}
          columns={columns}
          groups={THERMAL_GROUPS}
          onCreate={handleCreateRow}
          onDelete={handleDeleteSelection}
        />
      )}
      ifRejected={(error) => <SimpleContent title={error?.toString()} />}
    />
  );
}

export default Thermal;
