import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { MRT_ColumnDef } from "material-react-table";
import { Box, Chip, Tooltip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import {
  Storage,
  getStorages,
  deleteStorages,
  createStorage,
  STORAGE_GROUPS,
} from "./utils";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";

function Storages() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);

  const storages = usePromiseWithSnackbarError(
    () => getStorages(study.id, areaId),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId],
    },
  );

  const { totalWithdrawalNominalCapacity, totalInjectionNominalCapacity } =
    useMemo(() => {
      if (!storages.data) {
        return {
          totalWithdrawalNominalCapacity: 0,
          totalInjectionNominalCapacity: 0,
        };
      }

      return storages.data.reduce(
        (acc, { withdrawalNominalCapacity, injectionNominalCapacity }) => {
          acc.totalWithdrawalNominalCapacity += withdrawalNominalCapacity;
          acc.totalInjectionNominalCapacity += injectionNominalCapacity;
          return acc;
        },
        {
          totalWithdrawalNominalCapacity: 0,
          totalInjectionNominalCapacity: 0,
        },
      );
    }, [storages]);

  const columns = useMemo<Array<MRT_ColumnDef<Storage>>>(
    () => [
      {
        accessorKey: "name",
        header: t("global.name"),
        muiTableHeadCellProps: {
          align: "left",
        },
        muiTableBodyCellProps: {
          align: "left",
        },
        size: 100,
        Cell: ({ renderedCellValue, row }) => {
          const storageId = row.original.id;
          return (
            <Box
              sx={{
                cursor: "pointer",
                "&:hover": {
                  color: "primary.main",
                  textDecoration: "underline",
                },
              }}
              onClick={() => navigate(`${location.pathname}/${storageId}`)}
            >
              {renderedCellValue}
            </Box>
          );
        },
      },
      {
        accessorKey: "group",
        header: t("global.group"),
        size: 50,
        filterVariant: "select",
        filterSelectOptions: [...STORAGE_GROUPS],
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
        accessorKey: "injectionNominalCapacity",
        header: t("study.modelization.storages.injectionNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t(
              "study.modelization.storages.injectionNominalCapacity.info",
            )}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        Cell: ({ cell }) => Math.floor(cell.getValue<number>()),
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {Math.floor(cell.getValue<number>())}
          </Box>
        ),
        Footer: () => (
          <Box color="warning.main">
            {Math.floor(totalInjectionNominalCapacity)}
          </Box>
        ),
      },
      {
        accessorKey: "withdrawalNominalCapacity",
        header: t("study.modelization.storages.withdrawalNominalCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t(
              "study.modelization.storages.withdrawalNominalCapacity.info",
            )}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {Math.floor(cell.getValue<number>())}
          </Box>
        ),
        Cell: ({ cell }) => Math.floor(cell.getValue<number>()),
        Footer: () => (
          <Box color="warning.main">
            {Math.floor(totalWithdrawalNominalCapacity)}
          </Box>
        ),
      },
      {
        accessorKey: "reservoirCapacity",
        header: t("study.modelization.storages.reservoirCapacity"),
        Header: ({ column }) => (
          <Tooltip
            title={t("study.modelization.storages.reservoirCapacity.info")}
            placement="top"
            arrow
          >
            <Box>{column.columnDef.header}</Box>
          </Tooltip>
        ),
        size: 100,
        Cell: ({ cell }) => `${cell.getValue<number>()}`,
      },
      {
        accessorKey: "efficiency",
        header: t("study.modelization.storages.efficiency"),
        size: 50,
        Cell: ({ cell }) => `${Math.floor(cell.getValue<number>() * 100)}`,
      },
      {
        accessorKey: "initialLevel",
        header: t("study.modelization.storages.initialLevel"),
        size: 50,
        Cell: ({ cell }) => `${Math.floor(cell.getValue<number>() * 100)}`,
      },
      {
        accessorKey: "initialLevelOptim",
        header: t("study.modelization.storages.initialLevelOptim"),
        size: 180,
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
    ],
    [
      location.pathname,
      navigate,
      t,
      totalInjectionNominalCapacity,
      totalWithdrawalNominalCapacity,
    ],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = ({ id, ...storage }: Storage) => {
    return createStorage(study.id, areaId, storage);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteStorages(study.id, areaId, ids);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={storages}
      ifPending={() => <SimpleLoader />}
      ifResolved={(data) => (
        <GroupedDataTable
          data={data}
          columns={columns}
          groups={STORAGE_GROUPS}
          onCreate={handleCreateRow}
          onDelete={handleDeleteSelection}
        />
      )}
      ifRejected={(error) => <SimpleContent title={error?.toString()} />}
    />
  );
}

export default Storages;
