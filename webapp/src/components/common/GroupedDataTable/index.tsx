/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import Box from "@mui/material/Box";
import AddIcon from "@mui/icons-material/Add";
import { Button, Tooltip } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import MaterialReactTable, {
  MRT_Row,
  MRT_RowSelectionState,
  MRT_ToggleDensePaddingButton,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  type MRT_ColumnDef,
} from "material-react-table";
import { useTranslation } from "react-i18next";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import CreateRowDialog from "./CreateRowDialog";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";

export type TRow = { id: string; name: string; group: string };

export interface GroupedDataTableProps<TData extends TRow> {
  data: TData[];
  columns: MRT_ColumnDef<TData>[];
  groups: string[];
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
  const navigate = useNavigate();
  const location = useLocation();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [tableData, setTableData] = useState(data);
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});

  useEffect(() => {
    setTableData(data);
  }, [data]);

  const isAnyRowSelected = useMemo(
    () => Object.values(rowSelection).some((value) => value),
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

  const handleRowClick = (row: MRT_Row<TData>) => {
    const clusterId = row.original.id;
    navigate(`${location.pathname}/${clusterId}`);
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
        }}
        enableGrouping
        enableRowSelection
        enableColumnDragging={false}
        enableColumnActions={false}
        positionToolbarAlertBanner="none"
        enableBottomToolbar={false}
        enableRowActions
        enableStickyFooter
        enableStickyHeader
        enablePagination={false}
        onRowSelectionChange={setRowSelection}
        state={{ rowSelection }}
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
            {isAnyRowSelected && onDelete && (
              <Tooltip title={t("global.delete")}>
                <Button
                  startIcon={<DeleteIcon />}
                  variant="outlined"
                  size="small"
                  onClick={() => setConfirmDialogOpen(true)}
                >
                  {t("global.delete")}
                </Button>
              </Tooltip>
            )}
          </Box>
        )}
        renderToolbarInternalActions={({ table }) => (
          <>
            <MRT_ToggleGlobalFilterButton table={table} />
            <MRT_ToggleFiltersButton table={table} />
            <MRT_ToggleDensePaddingButton table={table} />
          </>
        )}
        renderRowActions={({ row }) => (
          <Tooltip title={t("global.view")}>
            <Box
              sx={{
                cursor: "pointer",
                "&:hover": {
                  color: "primary.main",
                  textDecoration: "underline",
                },
              }}
              onClick={() => handleRowClick(row)}
            >
              {row.original.name}
            </Box>
          </Tooltip>
        )}
        displayColumnDefOptions={{
          "mrt-row-actions": {
            header: "", // hide "Actions" column header
            size: 50,
            muiTableBodyCellProps: {
              align: "left",
            },
          },
        }}
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
