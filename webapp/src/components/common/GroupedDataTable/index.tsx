/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import DeleteIcon from "@mui/icons-material/Delete";
import { Box, Button, Skeleton } from "@mui/material";
import {
  MaterialReactTable,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  useMaterialReactTable,
  type MRT_RowSelectionState,
  type MRT_ColumnDef,
} from "material-react-table";
import { useTranslation } from "react-i18next";
import { useEffect, useMemo, useRef, useState } from "react";
import CreateDialog from "./CreateDialog";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import { generateUniqueValue, getTableOptionsForAlign } from "./utils";
import DuplicateDialog from "./DuplicateDialog";
import { translateWithColon } from "../../../utils/i18nUtils";
import useUpdatedRef from "../../../hooks/useUpdatedRef";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import type { PromiseAny } from "../../../utils/tsUtils";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../utils/fnUtils";
import useOperationInProgressCount from "../../../hooks/useOperationInProgressCount";
import type { TRow } from "./types";

export interface GroupedDataTableProps<
  TGroups extends string[],
  TData extends TRow<TGroups[number]>,
> {
  data: TData[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: Array<MRT_ColumnDef<TData, any>>;
  groups: TGroups;
  onCreate?: (values: TRow<TGroups[number]>) => Promise<TData>;
  onDuplicate?: (row: TData, newName: string) => Promise<TData>;
  onDelete?: (rows: TData[]) => PromiseAny | void;
  onNameClick?: (row: TData) => void;
  onDataChange?: (data: TData[]) => void;
  isLoading?: boolean;
  deleteConfirmationMessage?: string | ((count: number) => string);
  fillPendingRow?: (pendingRow: TRow<TGroups[number]>) => TRow<TGroups[number]> & Partial<TData>;
}

// Use ids to identify default columns (instead of `accessorKey`),
// to have a unique identifier. It is more likely to have a duplicate
// `accessorKey` with `columns` prop.
const GROUP_COLUMN_ID = "_group";
const NAME_COLUMN_ID = "_name";

function GroupedDataTable<TGroups extends string[], TData extends TRow<TGroups[number]>>({
  data,
  columns,
  groups,
  onCreate,
  onDuplicate,
  onDelete,
  onNameClick,
  onDataChange,
  isLoading,
  deleteConfirmationMessage,
  fillPendingRow,
}: GroupedDataTableProps<TGroups, TData>) {
  const { t } = useTranslation();
  const [openDialog, setOpenDialog] = useState<"add" | "duplicate" | "delete" | "">("");
  const [tableData, setTableData] = useState(data);
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  // Allow to use the last root of `onNameClick` in `tableColumns`
  const callbacksRef = useUpdatedRef({ onNameClick });
  const pendingRows = useRef<Array<TRow<TGroups[number]>>>([]);
  const { createOps, deleteOps, totalOps } = useOperationInProgressCount();

  useEffect(() => setTableData(data), [data]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => onDataChange?.(tableData), [tableData]);

  const existingNames = useMemo(() => tableData.map((row) => row.name.toLowerCase()), [tableData]);

  const tableColumns = useMemo<Array<MRT_ColumnDef<TData>>>(
    () => [
      {
        accessorKey: "group",
        header: t("global.group"),
        id: GROUP_COLUMN_ID,
        size: 50,
        filterVariant: "autocomplete",
        filterSelectOptions: groups,
        footer: translateWithColon("global.total"),
        ...getTableOptionsForAlign("left"),
      },
      {
        accessorKey: "name",
        header: t("global.name"),
        id: NAME_COLUMN_ID,
        size: 100,
        filterVariant: "autocomplete",
        filterSelectOptions: existingNames,
        Cell:
          callbacksRef.current.onNameClick &&
          (({ renderedCellValue, row }) => {
            if (isPendingRow(row.original)) {
              return renderedCellValue;
            }

            return (
              <Box
                sx={{
                  display: "inline",
                  "&:hover": {
                    color: "primary.main",
                    textDecoration: "underline",
                  },
                }}
                onClick={() => callbacksRef.current.onNameClick?.(row.original)}
              >
                {renderedCellValue}
              </Box>
            );
          }),
        ...getTableOptionsForAlign("left"),
      },
      ...columns.map(
        (column) =>
          ({
            ...column,
            Cell: (props) => {
              const { row, renderedCellValue } = props;
              // Use JSX instead of call it directly to remove React warning:
              // 'Warning: Internal React error: Expected static flag was missing.'
              const CellComp = column.Cell;

              if (isPendingRow(row.original)) {
                return <Skeleton width={80} height={24} sx={{ display: "inline-block" }} />;
              }

              return CellComp ? <CellComp {...props} /> : renderedCellValue;
            },
          }) as MRT_ColumnDef<TData>,
      ),
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns, t, ...groups],
  );

  const table = useMaterialReactTable({
    data: tableData,
    columns: tableColumns,
    initialState: {
      grouping: [GROUP_COLUMN_ID],
      density: "compact",
      expanded: true,
      columnPinning: { left: [GROUP_COLUMN_ID] },
    },
    state: { isLoading, isSaving: totalOps > 0, rowSelection },
    enableGrouping: true,
    enableStickyFooter: true,
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    // Rows
    muiTableBodyRowProps: ({ row }) => {
      const isPending = isPendingRow(row.original);

      return {
        onClick: () => {
          if (isPending) {
            return;
          }

          const isGrouped = row.getIsGrouped();
          const rowIds = isGrouped ? row.getLeafRows().map((r) => r.id) : [row.id];

          setRowSelection((prev) => {
            const newValue = isGrouped
              ? !rowIds.some((id) => prev[id]) // Select/Deselect all
              : !prev[row.id];

            return {
              ...prev,
              ...rowIds.reduce((acc, id) => ({ ...acc, [id]: newValue }), {}),
            };
          });
        },
        selected: rowSelection[row.id],
        sx: { cursor: isPending ? "wait" : "pointer" },
      };
    },
    // Toolbars
    renderTopToolbarCustomActions: ({ table }) => (
      <Box sx={{ display: "flex", gap: 1 }}>
        {onCreate && (
          <Button
            startIcon={<AddCircleOutlineIcon />}
            variant="contained"
            onClick={() => setOpenDialog("add")}
          >
            {t("button.add")}
          </Button>
        )}
        {onDuplicate && (
          <Button
            startIcon={<ContentCopyIcon />}
            variant="outlined"
            onClick={() => setOpenDialog("duplicate")}
            disabled={table.getSelectedRowModel().rows.length !== 1}
          >
            {t("global.duplicate")}
          </Button>
        )}
        {onDelete && (
          <Button
            startIcon={<DeleteOutlineIcon />}
            color="error"
            variant="outlined"
            onClick={() => setOpenDialog("delete")}
            disabled={table.getSelectedRowModel().rows.length === 0}
          >
            {t("global.delete")}
          </Button>
        )}
      </Box>
    ),
    renderToolbarInternalActions: ({ table }) => (
      <>
        <MRT_ToggleGlobalFilterButton table={table} />
        <MRT_ToggleFiltersButton table={table} />
      </>
    ),
    onRowSelectionChange: setRowSelection,
    // Styles
    muiTablePaperProps: { sx: { display: "flex", flexDirection: "column" } }, // Allow to have scroll
    ...R.mergeDeepRight(getTableOptionsForAlign("right"), {
      muiTableBodyCellProps: {
        sx: { borderBottom: "1px solid rgba(224, 224, 224, 0.3)" },
      },
    }),
  });

  const selectedRows = table.getSelectedRowModel().rows.map((row) => row.original);
  const selectedRow = selectedRows.length === 1 ? selectedRows[0] : null;

  ////////////////////////////////////////////////////////////////
  // Optimistic
  ////////////////////////////////////////////////////////////////

  const addPendingRow = (row: TRow<TGroups[number]>) => {
    const pendingRow = fillPendingRow?.(row) || row;

    pendingRows.current.push(pendingRow);

    // Type can be asserted as `TData` because the row will be checked in cell renders
    // and `fillPendingRow` allows to add needed data
    setTableData((prev) => [...prev, pendingRow as TData]);

    return pendingRow;
  };

  const removePendingRow = (row: TRow<TGroups[number]>) => {
    if (isPendingRow(row)) {
      pendingRows.current = pendingRows.current.filter((r) => r !== row);
      setTableData((prev) => prev.filter((r) => r !== row));
    }
  };

  function isPendingRow(row: TRow<TGroups[number]>) {
    return pendingRows.current.includes(row);
  }

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TRow<TGroups[number]>) => {
    closeDialog();

    if (!onCreate) {
      return;
    }

    createOps.increment();
    const pendingRow = addPendingRow(values);

    try {
      const newRow = await onCreate(values);
      setTableData((prev) => [...prev, newRow]);
    } catch (error) {
      enqueueErrorSnackbar(t("global.error.create"), toError(error));
    }

    removePendingRow(pendingRow);
    createOps.decrement();
  };

  const handleDuplicate = async (newName: string) => {
    closeDialog();

    if (!onDuplicate || !selectedRow) {
      return;
    }

    setRowSelection({});

    const duplicatedRow = {
      ...selectedRow,
      name: newName,
    };

    createOps.increment();
    const pendingRow = addPendingRow(duplicatedRow);

    try {
      const newRow = await onDuplicate(selectedRow, newName);
      setTableData((prev) => [...prev, newRow]);
    } catch (error) {
      enqueueErrorSnackbar(t("global.error.create"), toError(error));
    }

    removePendingRow(pendingRow);
    createOps.decrement();
  };

  const handleDelete = async () => {
    closeDialog();

    if (!onDelete) {
      return;
    }

    setRowSelection({});

    const rowsToDelete = selectedRows;

    setTableData((prevTableData) => prevTableData.filter((row) => !rowsToDelete.includes(row)));

    deleteOps.increment();

    try {
      await onDelete(rowsToDelete);
    } catch (error) {
      enqueueErrorSnackbar(t("global.error.delete"), toError(error));
      setTableData((prevTableData) => [...prevTableData, ...rowsToDelete]);
    }

    deleteOps.decrement();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <MaterialReactTable table={table} />
      {openDialog === "add" && (
        <CreateDialog
          open
          onClose={closeDialog}
          groups={groups}
          existingNames={existingNames}
          onSubmit={handleCreate}
        />
      )}
      {openDialog === "duplicate" && selectedRow && (
        <DuplicateDialog
          open
          onClose={closeDialog}
          onSubmit={handleDuplicate}
          existingNames={existingNames}
          defaultName={generateUniqueValue(selectedRow.name, tableData)}
        />
      )}
      {openDialog === "delete" && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          title={t("dialog.title.confirmation")}
          onCancel={closeDialog}
          onConfirm={handleDelete}
          alert="warning"
        >
          {RA.isFunction(deleteConfirmationMessage)
            ? deleteConfirmationMessage(selectedRows.length)
            : (deleteConfirmationMessage ?? t("dialog.message.confirmDelete"))}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default GroupedDataTable;
