/* eslint-disable camelcase */
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { MRT_ColumnDef } from "material-react-table";
import { Box, Chip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import {
  Storage,
  StorageGroup,
  getStorages,
  deleteStorages,
  STORAGE_GROUP_OPTIONS,
  createStorage,
} from "./utils";
import SimpleContent from "../../../../../../common/page/SimpleContent";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";

function Storages() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const currentAreaId = useAppSelector(getCurrentAreaId);
  const groups = Object.values(StorageGroup);

  const storages = usePromiseWithSnackbarError(
    () => getStorages(study.id, currentAreaId),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, currentAreaId],
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

  const columns = useMemo<MRT_ColumnDef<Storage>[]>(
    () => [
      {
        accessorKey: "name",
        header: "Name",
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
        header: "Group",
        size: 50,
        filterVariant: "select",
        filterSelectOptions: STORAGE_GROUP_OPTIONS,
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
        header: "Nominal capacity",
        size: 50,
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<number>()}
          </Box>
        ),
        Footer: () => (
          <Box color="warning.main">{totalInjectionNominalCapacity}</Box>
        ),
      },
      {
        accessorKey: "withdrawalNominalCapacity",
        header: "Withdrawal capacity",
        size: 50,
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {cell.getValue<number>()}
          </Box>
        ),
        Footer: () => (
          <Box color="warning.main">{totalWithdrawalNominalCapacity}</Box>
        ),
      },
      {
        accessorKey: "reservoirCapacity",
        header: "Reservoir capacity",
        size: 50,
        Cell: ({ cell }) => `${cell.getValue<number>() * 100} MWh`,
      },
      {
        accessorKey: "efficiency",
        header: "Efficiency",
        size: 50,
        Cell: ({ cell }) => `${cell.getValue<number>() * 100} %`,
      },
      {
        accessorKey: "initialLevel",
        header: "Initial Level",
        size: 50,
      },
      {
        accessorKey: "initialLevelOptim",
        header: "Initial Level Optim",
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
    ],
    [
      location.pathname,
      navigate,
      totalInjectionNominalCapacity,
      totalWithdrawalNominalCapacity,
    ],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = ({ id, ...storage }: Storage) => {
    return createStorage(study.id, currentAreaId, storage);
  };

  const handleDeleteSelection = (ids: string[]) => {
    return deleteStorages(study.id, currentAreaId, ids);
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
          groups={groups}
          onCreate={handleCreateRow}
          onDelete={handleDeleteSelection}
        />
      )}
      ifRejected={(error) => <SimpleContent title={error?.toString()} />}
    />
  );
}

export default Storages;
