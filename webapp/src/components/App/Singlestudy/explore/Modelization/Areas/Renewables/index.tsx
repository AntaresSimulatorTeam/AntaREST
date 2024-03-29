import { useMemo } from "react";
import { MRT_ColumnDef } from "material-react-table";
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
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

function Renewables() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const areaId = useAppSelector(getCurrentAreaId);
  const navigate = useNavigate();
  const location = useLocation();

  const {
    clusters,
    clustersWithCapacity,
    totalUnitCount,
    totalInstalledCapacity,
    totalEnabledCapacity,
  } = useClusterDataWithCapacity<RenewableCluster>(
    () => getRenewableClusters(study.id, areaId),
    t("studies.error.retrieveData"),
    [study.id, areaId],
  );

  const columns = useMemo<Array<MRT_ColumnDef<RenewableClusterWithCapacity>>>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
        muiTableHeadCellProps: {
          align: "left",
        },
        muiTableBodyCellProps: {
          align: "left",
        },
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
        filterSelectOptions: [...RENEWABLE_GROUPS],
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
        accessorKey: "tsInterpretation",
        header: "TS Interpretation",
        size: 50,
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
        Cell: ({ cell }) => Math.floor(cell.getValue<number>()),
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
  }: RenewableClusterWithCapacity) => {
    return createRenewableCluster(study.id, areaId, cluster);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteRenewableClusters(study.id, areaId, ids);
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
          groups={RENEWABLE_GROUPS}
          onCreate={handleCreateRow}
          onDelete={handleDeleteSelection}
        />
      )}
      ifRejected={(error) => <SimpleContent title={error?.toString()} />}
    />
  );
}

export default Renewables;
