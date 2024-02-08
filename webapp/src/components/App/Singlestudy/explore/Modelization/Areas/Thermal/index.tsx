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
  ThermalClusterWithCapacity,
  THERMAL_GROUPS,
  ThermalCluster,
} from "./utils";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import {
  capacityAggregationFn,
  useClusterDataWithCapacity,
} from "../common/utils";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

function Thermal() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);

  const {
    clusters,
    clustersWithCapacity,
    totalUnitCount,
    totalInstalledCapacity,
    totalEnabledCapacity,
  } = useClusterDataWithCapacity<ThermalCluster>(
    () => getThermalClusters(study.id, areaId),
    t("studies.error.retrieveData"),
    [study.id, areaId],
  );

  const columns = useMemo<Array<MRT_ColumnDef<ThermalClusterWithCapacity>>>(
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
            label={cell.getValue<boolean>() ? t("button.yes") : t("button.no")}
            color={cell.getValue<boolean>() ? "success" : "error"}
            size="small"
            sx={{ minWidth: 40 }}
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
            label={cell.getValue<boolean>() ? t("button.yes") : t("button.no")}
            color={cell.getValue<boolean>() ? "success" : "error"}
            size="small"
            sx={{ minWidth: 40 }}
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
        Cell: ({ cell }) => cell.getValue<number>().toFixed(1),
      },
      {
        accessorKey: "installedCapacity",
        header: "Enabled / Installed (MW)",
        size: 200,
        aggregationFn: capacityAggregationFn(),
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<string>() ?? ""}
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
      t,
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
    return createThermalCluster(study.id, areaId, cluster);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteThermalClusters(study.id, areaId, ids);
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
