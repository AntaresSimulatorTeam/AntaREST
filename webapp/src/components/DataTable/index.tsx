/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import { isQueryListItemOptimistic } from "@/queries/utils";
import { appendColon } from "@/utils/i18nUtils";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteIcon from "@mui/icons-material/Delete";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { Box, Button, Skeleton } from "@mui/material";
import { type ToOptions } from "@tanstack/react-router";
import {
  MaterialReactTable,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  useMaterialReactTable,
  type MRT_ColumnDef,
  type MRT_RowSelectionState,
} from "material-react-table";
import * as RA from "ramda-adjunct";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLatest } from "react-use";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import RouterLink from "../router/RouterLink";
import CreateDialog from "./CreateDialog";
import DuplicateDialog from "./DuplicateDialog";
import type { RowData } from "./types";
import { generateUniqueValue, getDarkModeFixStyles, getTableOptionsForAlign } from "./utils";

export interface DataTableProps<TData extends RowData> {
  data: TData[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columns: Array<MRT_ColumnDef<TData, any>>;
  /**
   * Omit to disable grouping. When omitted, the group column and grouping
   * behavior are removed and the create dialog skips the group field.
   */
  groups?: string[];
  allowNewGroups?: boolean;
  onCreate?: (values: RowData | (RowData & Partial<TData>)) => void;
  /**
   * Render a custom create dialog instead of the built-in one.
   * Useful when creation requires fields the built-in dialog doesn't handle.
   */
  renderCreateDialog?: (props: {
    open: boolean;
    onClose: VoidFunction;
    onSubmit: (values: RowData & Partial<TData>) => void;
    existingNames: Array<RowData["name"]>;
  }) => React.ReactNode;
  onDuplicate?: (row: TData, newName: string) => void;
  onDelete?: (rows: TData[]) => void;
  onNameClick?: (row: TData) => void;
  nameLinkOptions?: (row: TData) => ToOptions;
  readOnly?: boolean;
  isLoading?: boolean;
  isSaving?: boolean;
  deleteConfirmationMessage?: string | ((rows: TData[]) => string);
  /**
   * Extra actions rendered next to the built-in Add/Duplicate/Delete buttons.
   */
  toolbarActions?: React.ReactNode;
}

// Use ids to identify default columns (instead of `accessorKey`),
// to have a unique identifier. It is more likely to have a duplicate
// `accessorKey` with `columns` prop.
const GROUP_COLUMN_ID = "_group";
const NAME_COLUMN_ID = "_name";

function DataTable<TData extends RowData>({
  data,
  columns,
  groups,
  allowNewGroups = false,
  onCreate,
  renderCreateDialog,
  onDuplicate,
  onDelete,
  onNameClick,
  nameLinkOptions,
  readOnly = false,
  isLoading,
  isSaving,
  deleteConfirmationMessage,
  toolbarActions,
}: DataTableProps<TData>) {
  const { t } = useTranslation();
  const [openDialog, setOpenDialog] = useState<"add" | "duplicate" | "delete" | "">("");
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});
  const callbacksRef = useLatest({ onNameClick, nameLinkOptions, readOnly });
  const { isDarkMode } = useThemeColorScheme();
  const existingNames = useMemo(() => data.map((row) => row.name.toLowerCase()), [data]);
  const hasGroups = groups !== undefined;

  const tableColumns = useMemo<Array<MRT_ColumnDef<TData>>>(() => {
    const groupColumn: MRT_ColumnDef<TData> = {
      accessorKey: "group",
      header: t("global.group"),
      id: GROUP_COLUMN_ID,
      size: 50,
      filterVariant: "autocomplete",
      filterSelectOptions: groups,
      footer: appendColon(t("global.total")),
      ...getTableOptionsForAlign("left"),
    };

    return [
      ...(hasGroups ? [groupColumn] : []),
      {
        accessorKey: "name",
        header: t("global.name"),
        id: NAME_COLUMN_ID,
        size: 100,
        filterVariant: "autocomplete",
        filterSelectOptions: existingNames,
        Cell: ({ renderedCellValue, row }) => {
          const { onNameClick, nameLinkOptions, readOnly } = callbacksRef.current;

          if (isQueryListItemOptimistic(row.original) || readOnly) {
            return renderedCellValue;
          }

          if (nameLinkOptions) {
            return (
              <RouterLink color="textPrimary" underline="hover" {...nameLinkOptions(row.original)}>
                {renderedCellValue}
              </RouterLink>
            );
          }

          if (onNameClick) {
            return (
              <Box
                sx={{
                  display: "inline",
                  "&:hover": {
                    color: "primary.main",
                    textDecoration: "underline",
                  },
                }}
                onClick={() => onNameClick(row.original)}
              >
                {renderedCellValue}
              </Box>
            );
          }

          return renderedCellValue;
        },
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

              if (isQueryListItemOptimistic(row.original)) {
                return <Skeleton width={80} height={24} sx={{ display: "inline-block" }} />;
              }

              return CellComp ? <CellComp {...props} /> : renderedCellValue;
            },
          }) as MRT_ColumnDef<TData>,
      ),
    ];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, t, hasGroups, ...(groups ?? [])]);

  const table = useMaterialReactTable({
    data,
    getRowId: (row) => row.id,
    columns: tableColumns,
    localization: { noRecordsToDisplay: t("global.noData") },
    initialState: {
      density: "compact",
      ...(hasGroups && {
        grouping: [GROUP_COLUMN_ID],
        expanded: true,
        columnPinning: { left: [GROUP_COLUMN_ID] },
      }),
    },
    state: {
      isLoading,
      isSaving,
      rowSelection,
    },
    enableGrouping: hasGroups,
    enableStickyFooter: true,
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    // Rows
    muiTableBodyRowProps: ({ row }) => {
      if (readOnly) {
        return {};
      }

      const isPending = isQueryListItemOptimistic(row.original);

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
    onRowSelectionChange: setRowSelection,
    // Toolbars
    renderTopToolbarCustomActions: ({ table }) => (
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        {onCreate && (
          <Button
            startIcon={<AddCircleOutlineIcon />}
            variant="contained"
            onClick={() => setOpenDialog("add")}
            disabled={readOnly}
          >
            {t("button.add")}
          </Button>
        )}
        {onDuplicate && (
          <Button
            startIcon={<ContentCopyIcon />}
            variant="outlined"
            onClick={() => setOpenDialog("duplicate")}
            disabled={readOnly || table.getSelectedRowModel().rows.length !== 1}
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
            disabled={readOnly || table.getSelectedRowModel().rows.length === 0}
          >
            {t("global.delete")}
          </Button>
        )}
        {toolbarActions}
      </Box>
    ),
    renderToolbarInternalActions: ({ table }) => (
      <>
        <MRT_ToggleGlobalFilterButton table={table} />
        <MRT_ToggleFiltersButton table={table} />
      </>
    ),
    positionToolbarDropZone: "none",
    muiSearchTextFieldProps: { size: "extra-small" },
    muiTopToolbarProps: {
      sx: {
        minHeight: "auto",
        overflowX: "auto",
        "> .MuiBox-root": {
          alignItems: "center",
          p: 0,
          pb: 1,
          "> .MuiBox-root": {
            flexWrap: "nowrap", // Prevent the search field to be wrapped
          },
        },
      },
    },
    // Styles
    muiTablePaperProps: { sx: { display: "flex", flexDirection: "column" } }, // Allow to have scroll
    ...getTableOptionsForAlign("right"),
    ...getDarkModeFixStyles(isDarkMode),
  });

  const selectedRows = table.getSelectedRowModel().rows.map((row) => row.original);
  const selectedRow = selectedRows.length === 1 ? selectedRows[0] : null;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = (values: RowData | (RowData & Partial<TData>)) => {
    onCreate?.(values);
  };

  const handleDuplicate = (newName: string) => {
    closeDialog();

    if (!onDuplicate || !selectedRow) {
      return;
    }

    setRowSelection({});

    onDuplicate(selectedRow, newName);
  };

  const handleDelete = () => {
    closeDialog();

    if (!onDelete) {
      return;
    }

    setRowSelection({});

    onDelete(selectedRows);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <MaterialReactTable table={table} />
      {openDialog === "add" &&
        (renderCreateDialog ? (
          renderCreateDialog({
            open: true,
            onClose: closeDialog,
            onSubmit: handleCreate,
            existingNames,
          })
        ) : (
          <CreateDialog
            open
            onClose={closeDialog}
            groups={groups}
            allowNewGroups={allowNewGroups}
            existingNames={existingNames}
            onSubmit={handleCreate}
          />
        ))}
      {openDialog === "duplicate" && selectedRow && (
        <DuplicateDialog
          open
          onClose={closeDialog}
          onSubmit={handleDuplicate}
          existingNames={existingNames}
          defaultName={generateUniqueValue(selectedRow.name, data)}
        />
      )}
      {openDialog === "delete" && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          title={t("dialog.title.confirmation")}
          onCancel={closeDialog}
          onConfirm={handleDelete}
          alert="error"
        >
          {RA.isFunction(deleteConfirmationMessage)
            ? deleteConfirmationMessage(selectedRows)
            : (deleteConfirmationMessage ?? t("dialog.message.confirmDelete"))}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default DataTable;
