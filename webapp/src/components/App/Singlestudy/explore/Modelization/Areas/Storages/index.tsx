import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { createMRTColumnHelper, type MRT_Row } from "material-react-table";
import { Box, Chip, Tooltip } from "@mui/material";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import GroupedDataTable from "../../../../../../common/GroupedDataTable";
import {
  Storage,
  getStorages,
  deleteStorages,
  createStorage,
  STORAGE_GROUPS,
  StorageGroup,
} from "./utils";
import usePromiseWithSnackbarError from "../../../../../../../hooks/usePromiseWithSnackbarError";
import type { TRow } from "../../../../../../common/GroupedDataTable/types";

function Storages() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const areaId = useAppSelector(getCurrentAreaId);
  const columnHelper = createMRTColumnHelper<Storage>();

  const { data: storages, isLoading } = usePromiseWithSnackbarError(
    () => getStorages(study.id, areaId),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId],
    },
  );

  const { totalWithdrawalNominalCapacity, totalInjectionNominalCapacity } =
    useMemo(() => {
      if (!storages) {
        return {
          totalWithdrawalNominalCapacity: 0,
          totalInjectionNominalCapacity: 0,
        };
      }

      return storages.reduce(
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

  const columns = useMemo(
    () => [
      columnHelper.accessor("injectionNominalCapacity", {
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
        aggregationFn: "sum",
        AggregatedCell: ({ cell }) => (
          <Box sx={{ color: "info.main", fontWeight: "bold" }}>
            {Math.floor(cell.getValue())}
          </Box>
        ),
        Cell: ({ cell }) => Math.floor(cell.getValue()),
        Footer: () => (
          <Box color="warning.main">
            {Math.floor(totalInjectionNominalCapacity)}
          </Box>
        ),
      }),
      columnHelper.accessor("withdrawalNominalCapacity", {
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
            {Math.floor(cell.getValue())}
          </Box>
        ),
        Cell: ({ cell }) => Math.floor(cell.getValue()),
        Footer: () => (
          <Box color="warning.main">
            {Math.floor(totalWithdrawalNominalCapacity)}
          </Box>
        ),
      }),
      columnHelper.accessor("reservoirCapacity", {
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
        Cell: ({ cell }) => `${cell.getValue()}`,
      }),
      columnHelper.accessor("efficiency", {
        header: t("study.modelization.storages.efficiency"),
        size: 50,
        Cell: ({ cell }) => `${Math.floor(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevel", {
        header: t("study.modelization.storages.initialLevel"),
        size: 50,
        Cell: ({ cell }) => `${Math.floor(cell.getValue() * 100)}`,
      }),
      columnHelper.accessor("initialLevelOptim", {
        header: t("study.modelization.storages.initialLevelOptim"),
        size: 200,
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
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, totalInjectionNominalCapacity, totalWithdrawalNominalCapacity],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = (values: TRow<StorageGroup>) => {
    return createStorage(study.id, areaId, values);
  };

  const handleDelete = (rows: Storage[]) => {
    const ids = rows.map((row) => row.id);
    return deleteStorages(study.id, areaId, ids);
  };

  const handleNameClick = (row: MRT_Row<Storage>) => {
    navigate(`${location.pathname}/${row.original.id}`);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupedDataTable
      isLoading={isLoading}
      data={storages || []}
      columns={columns}
      groups={[...STORAGE_GROUPS]}
      onCreate={handleCreate}
      onDelete={handleDelete}
      onNameClick={handleNameClick}
      deleteConfirmationMessage={(count) =>
        t("studies.modelization.clusters.question.delete", { count })
      }
    />
  );
}

export default Storages;
