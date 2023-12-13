/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import Box from "@mui/material/Box";
import AddIcon from "@mui/icons-material/Add";
import { Button } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  MaterialReactTable,
  MRT_RowSelectionState,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  type MRT_ColumnDef,
} from "material-react-table";
import { useTranslation } from "react-i18next";
import { useMemo, useState } from "react";
import CreateRowDialog from "./CreateRowDialog";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import { generateUniqueValue } from "./utils";

export type TRow = { id: string; name: string; group: string };

export interface GroupedDataTableProps<TData extends TRow> {
  data: TData[];
  columns: MRT_ColumnDef<TData>[];
  groups: string[] | readonly string[];
  onCreate?: (values: TData) => Promise<TData>;
  onDelete?: (ids: string[]) => void;
}

function GroupedDataTable<TData extends TRow>({
  data,
  columns,
  groups,
  onCreate,
  onDelete,
}: GroupedDataTableProps<TData>) {
  const { t } = useTranslation();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [tableData, setTableData] = useState(data);
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});

  const isAnyRowSelected = useMemo(
    () => Object.values(rowSelection).some((value) => value),
    [rowSelection],
  );

  const isOneRowSelected = useMemo(
    () => Object.values(rowSelection).filter((value) => value).length === 1,
    [rowSelection],
  );

  const existingNames = useMemo(
    () => tableData.map((row) => row.name.toLowerCase()),
    [tableData],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreateRow = async (values: TData) => {
    if (onCreate) {
      const newRow = await onCreate(values);
      setTableData((prevTableData) => [...prevTableData, newRow]);
    }
  };

  const handleDeleteSelection = () => {
    if (!onDelete) {
      return;
    }

    const rowIndexes = Object.keys(rowSelection)
      .map(Number)
      // ignore groups names
      .filter(Number.isInteger);

    const rowIdsToDelete = rowIndexes.map((index) => tableData[index].id);

    onDelete(rowIdsToDelete);
    setTableData((prevTableData) =>
      prevTableData.filter((row) => !rowIdsToDelete.includes(row.id)),
    );
    setRowSelection({});
    setConfirmDialogOpen(false);
  };

  const handleDuplicateRow = async () => {
    const selectedIndex = Object.keys(rowSelection).find(
      (key) => rowSelection[key],
    );
    const selectedRow = selectedIndex && tableData[+selectedIndex];

    if (!selectedRow) {
      return;
    }

    const name = generateUniqueValue("name", selectedRow.name, tableData);
    const id = generateUniqueValue("id", name, tableData);

    const duplicatedRow = {
      ...selectedRow,
      id,
      name,
    };

    if (onCreate) {
      const newRow = await onCreate(duplicatedRow);
      setTableData((prevTableData) => [...prevTableData, newRow]);
      setRowSelection({});
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <MaterialReactTable
        data={tableData}
        columns={columns}
        initialState={{
          grouping: ["group"],
          density: "compact",
          expanded: true,
          columnPinning: { left: ["group"] },
        }}
        enablePinning
        enableExpanding
        enableGrouping
        muiTableBodyRowProps={({ row: { id, groupingColumnId } }) => {
          const handleRowClick = () => {
            // prevent group rows to be selected
            if (groupingColumnId === undefined) {
              setRowSelection((prev) => ({
                ...prev,
                [id]: !prev[id],
              }));
            }
          };

          return {
            onClick: handleRowClick,
            selected: rowSelection[id],
            sx: {
              cursor: "pointer",
            },
          };
        }}
        state={{ rowSelection }}
        enableColumnDragging={false}
        enableColumnActions={false}
        positionToolbarAlertBanner="none"
        enableBottomToolbar={false}
        enableStickyFooter
        enableStickyHeader
        enablePagination={false}
        renderTopToolbarCustomActions={() => (
          <Box sx={{ display: "flex", gap: 1 }}>
            {onCreate && (
              <Button
                startIcon={<AddIcon />}
                variant="contained"
                size="small"
                onClick={() => setCreateDialogOpen(true)}
              >
                {t("button.add")}
              </Button>
            )}
            <Button
              startIcon={<ContentCopyIcon />}
              variant="outlined"
              size="small"
              onClick={handleDuplicateRow}
              disabled={!isOneRowSelected}
            >
              {t("global.duplicate")}
            </Button>
            {onDelete && (
              <Button
                startIcon={<DeleteIcon />}
                variant="outlined"
                size="small"
                onClick={() => setConfirmDialogOpen(true)}
                disabled={!isAnyRowSelected}
              >
                {t("global.delete")}
              </Button>
            )}
          </Box>
        )}
        renderToolbarInternalActions={({ table }) => (
          <>
            <MRT_ToggleGlobalFilterButton table={table} />
            <MRT_ToggleFiltersButton table={table} />
          </>
        )}
        muiTableHeadCellProps={{
          align: "right",
        }}
        muiTableBodyCellProps={{
          align: "right",
          sx: {
            borderBottom: "1px solid rgba(224, 224, 224, 0.3)",
          },
        }}
        muiTableFooterCellProps={{
          align: "right",
        }}
        muiTablePaperProps={{
          sx: {
            width: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "auto",
          },
        }}
      />
      {createDialogOpen && (
        <CreateRowDialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          groups={groups}
          existingNames={existingNames}
          onSubmit={handleCreateRow}
        />
      )}
      {confirmDialogOpen && (
        <ConfirmationDialog
          title={t("dialog.title.confirmation")}
          onCancel={() => setConfirmDialogOpen(false)}
          onConfirm={handleDeleteSelection}
          alert="warning"
          open
        >
          {t("studies.modelization.clusters.question.delete")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default GroupedDataTable;
