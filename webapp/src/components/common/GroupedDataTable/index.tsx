/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import Box from "@mui/material/Box";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ControlPointDuplicateIcon from "@mui/icons-material/ControlPointDuplicate";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import {
  MaterialReactTable,
  MRT_RowSelectionState,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  type MRT_ColumnDef,
} from "material-react-table";
import { useTranslation } from "react-i18next";
import { useMemo, useState } from "react";
import CreateDialog from "./CreateDialog";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import { TRow, generateUniqueValue } from "./utils";
import DuplicateDialog from "./DuplicateDialog";

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
  const [openDialog, setOpenDialog] = useState<
    "add" | "duplicate" | "delete" | ""
  >("");
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

  const selectedRow = useMemo(() => {
    if (isOneRowSelected) {
      const selectedIndex = Object.keys(rowSelection).find(
        (key) => rowSelection[key],
      );
      return selectedIndex && tableData[+selectedIndex];
    }
  }, [isOneRowSelected, rowSelection, tableData]);

  const existingNames = useMemo(
    () => tableData.map((row) => row.name.toLowerCase()),
    [tableData],
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async (values: TData) => {
    if (onCreate) {
      const newRow = await onCreate(values);
      setTableData((prevTableData) => [...prevTableData, newRow]);
    }
  };

  const handleDelete = () => {
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
    closeDialog();
  };

  const handleDuplicate = async (name: string) => {
    if (!selectedRow) {
      return;
    }

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
                startIcon={<AddCircleOutlineIcon />}
                variant="contained"
                size="small"
                onClick={() => setOpenDialog("add")}
              >
                {t("button.add")}
              </Button>
            )}
            <Button
              startIcon={<ControlPointDuplicateIcon />}
              variant="outlined"
              size="small"
              onClick={() => setOpenDialog("duplicate")}
              disabled={!isOneRowSelected}
            >
              {t("global.duplicate")}
            </Button>
            {onDelete && (
              <Button
                startIcon={<DeleteOutlineIcon />}
                variant="outlined"
                size="small"
                onClick={() => setOpenDialog("delete")}
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
          defaultName={generateUniqueValue("name", selectedRow.name, tableData)}
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
          {t("studies.modelization.clusters.question.delete")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default GroupedDataTable;
