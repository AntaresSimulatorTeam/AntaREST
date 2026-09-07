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

import { getDarkModeFixStyles, getTableOptionsForAlign } from "@/components/GroupedDataTable/utils";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import AddIcon from "@mui/icons-material/Add";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import RedoIcon from "@mui/icons-material/Redo";
import RemoveIcon from "@mui/icons-material/Remove";
import SaveIcon from "@mui/icons-material/Save";
import UndoIcon from "@mui/icons-material/Undo";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Alert, Box, Button, Checkbox, IconButton, Stack, TextField, Tooltip } from "@mui/material";
import {
  createMRTColumnHelper,
  MaterialReactTable,
  MRT_ExpandButton,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  useMaterialReactTable,
  type MRT_RowSelectionState,
} from "material-react-table";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ClusterGroup } from "./types";
import type { SymmetryValidationError } from "./utils";

interface SymmetryDataRow {
  kind: "symmetry";
  id: string;
  uiId: string;
  clusterId: string;
  index: number;
  reserves: Set<string>;
}

interface ClusterHeaderRow {
  kind: "cluster";
  id: string;
  clusterId: string;
  clusterName: string;
  subRows: SymmetryDataRow[];
}

type SymmetriesTableRow = ClusterHeaderRow | SymmetryDataRow;

interface Props {
  groups: ClusterGroup[];
  reserves: Reserve[];
  certifiedReservesByCluster: Map<string, Set<string>>;
  validationErrors: SymmetryValidationError[];
  readOnly?: boolean;
  isFetching?: boolean;
  canUndo: boolean;
  canRedo: boolean;
  canSave: boolean;
  isSaving?: boolean;
  onAddSymmetries: (clusterId: string, count: number) => void;
  onDeleteRows: (uiIds: Set<string>) => void;
  onDuplicateRow: (uiId: string) => void;
  onToggleReserve: (uiId: string, reserveId: string) => void;
  onUndo: VoidFunction;
  onRedo: VoidFunction;
  onSave: VoidFunction;
}

const columnHelper = createMRTColumnHelper<SymmetriesTableRow>();

// Displays clusters as parent rows and their symmetries as sub-rows, one
// column per reserve, each cell a checkbox toggling that symmetry's
// participation in that reserve.
function SymmetriesTable({
  groups,
  reserves,
  certifiedReservesByCluster,
  validationErrors,
  readOnly,
  isFetching,
  canUndo,
  canRedo,
  canSave,
  isSaving,
  onAddSymmetries,
  onDeleteRows,
  onDuplicateRow,
  onToggleReserve,
  onUndo,
  onRedo,
  onSave,
}: Props) {
  const { t } = useTranslation();
  const { isDarkMode } = useThemeColorScheme();
  const [rowSelection, setRowSelection] = useState<MRT_RowSelectionState>({});
  // Raw input string, clamping on each keystroke would fight typing;
  // `symmetryCount` is the normalized value actually used.
  const [symmetryCountInput, setSymmetryCountInput] = useState("1");
  const symmetryCount = R.clamp(1, 100, Math.floor(Number(symmetryCountInput)) || 1);

  const rows = useMemo<ClusterHeaderRow[]>(
    () =>
      groups.map((group) => ({
        kind: "cluster",
        id: group.clusterId,
        clusterId: group.clusterId,
        clusterName: group.clusterName,
        subRows: group.symmetries.map((row) => ({
          kind: "symmetry",
          id: row.uiId,
          uiId: row.uiId,
          clusterId: group.clusterId,
          index: row.index,
          reserves: row.reserves,
        })),
      })),
    [groups],
  );

  const invalidUiIds = useMemo(
    () => new Set(validationErrors.map((error) => error.uiId)),
    [validationErrors],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor(
        (row) =>
          row.kind === "cluster"
            ? row.clusterName
            : t("study.modeling.reserves.symmetries.symmetryName", { index: row.index }),
        {
          id: "name",
          header: t("global.name"),
          size: 160,
          Cell: ({ renderedCellValue, row, staticRowIndex, table }) => (
            <Stack direction="row" alignItems="center" gap={0.5}>
              <MRT_ExpandButton row={row} staticRowIndex={staticRowIndex} table={table} />
              {renderedCellValue}
              {row.original.kind === "symmetry" && invalidUiIds.has(row.original.uiId) && (
                <Tooltip title={t("study.modeling.reserves.symmetries.invalidRow")}>
                  <WarningAmberIcon color="warning" sx={{ fontSize: 16 }} />
                </Tooltip>
              )}
            </Stack>
          ),
          ...getTableOptionsForAlign("left"),
        },
      ),
      ...reserves.map((reserve) =>
        columnHelper.accessor(
          (row) => (row.kind === "symmetry" ? row.reserves.has(reserve.id) : null),
          {
            id: reserve.id,
            header: reserve.name,
            size: 90,
            Cell: ({ row, cell }) => {
              const original = row.original;

              if (original.kind !== "symmetry") {
                return null;
              }

              const isCertified =
                certifiedReservesByCluster.get(original.clusterId)?.has(reserve.id) ?? false;

              return (
                <Tooltip
                  title={
                    isCertified ? "" : t("study.modeling.reserves.symmetries.notCertifiedTooltip")
                  }
                >
                  <span>
                    <Checkbox
                      size="small"
                      checked={cell.getValue<boolean | null>() === true}
                      disabled={readOnly || !isCertified}
                      onChange={() => onToggleReserve(original.uiId, reserve.id)}
                    />
                  </span>
                </Tooltip>
              );
            },
          },
        ),
      ),
    ],
    [reserves, certifiedReservesByCluster, invalidUiIds, readOnly, onToggleReserve, t],
  );

  const table = useMaterialReactTable({
    data: rows,
    columns,
    getRowId: (row) => row.id,
    getSubRows: (row) => (row.kind === "cluster" ? row.subRows : undefined),
    enableExpanding: true,
    enableRowSelection: true,
    enableMultiRowSelection: true,
    // Cluster and symmetry rows are two independent selection states
    // selecting a cluster row must not implicitly select its symmetries.
    enableSubRowSelection: false,
    filterFromLeafRows: true,
    initialState: {
      density: "compact",
      expanded: true,
      columnVisibility: { "mrt-row-expand": false },
    },
    // Data is always present (suspense queries): refetches show progress
    // bars, not a blanking skeleton.
    state: { showProgressBars: isFetching, rowSelection },
    onRowSelectionChange: setRowSelection,
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    positionToolbarDropZone: "none",
    renderTopToolbarCustomActions: ({ table }) => {
      const selectedRows = table.getSelectedRowModel().rows.map((row) => row.original);
      const selectedClusters = selectedRows.filter(
        (row): row is ClusterHeaderRow => row.kind === "cluster",
      );
      const selectedSymmetries = selectedRows.filter(
        (row): row is SymmetryDataRow => row.kind === "symmetry",
      );
      const isSingleClusterSelected = selectedRows.length === 1 && selectedClusters.length === 1;
      const isSingleSymmetrySelected = selectedRows.length === 1 && selectedSymmetries.length === 1;
      const isOnlySymmetriesSelected =
        selectedRows.length > 0 && selectedSymmetries.length === selectedRows.length;

      const isCountDisabled = readOnly || !isSingleClusterSelected;

      return (
        <Stack direction="row" gap={1} alignItems="center" flexWrap="wrap">
          <Stack direction="row" alignItems="center">
            <IconButton
              size="small"
              disabled={isCountDisabled || symmetryCount <= 1}
              onClick={() => setSymmetryCountInput(String(symmetryCount - 1))}
            >
              <RemoveIcon fontSize="small" />
            </IconButton>
            <TextField
              size="small"
              type="number"
              value={symmetryCountInput}
              onChange={(e) => setSymmetryCountInput(e.target.value)}
              onBlur={() => setSymmetryCountInput(String(symmetryCount))}
              slotProps={{ htmlInput: { min: 1, max: 100 } }}
              disabled={isCountDisabled}
              sx={{ width: 70 }}
            />
            <IconButton
              size="small"
              disabled={isCountDisabled || symmetryCount >= 100}
              onClick={() => setSymmetryCountInput(String(symmetryCount + 1))}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Stack>
          <Button
            startIcon={<AddCircleOutlineIcon />}
            variant="contained"
            disabled={readOnly || !isSingleClusterSelected}
            onClick={() => onAddSymmetries(selectedClusters[0].clusterId, symmetryCount)}
          >
            {t("study.modeling.reserves.symmetries.add")}
          </Button>
          <Button
            startIcon={<ContentCopyIcon />}
            variant="outlined"
            disabled={readOnly || !isSingleSymmetrySelected}
            onClick={() => onDuplicateRow(selectedSymmetries[0].uiId)}
          >
            {t("global.duplicate")}
          </Button>
          <Button
            startIcon={<DeleteOutlineIcon />}
            color="error"
            variant="outlined"
            disabled={readOnly || !isOnlySymmetriesSelected}
            onClick={() => {
              onDeleteRows(new Set(selectedSymmetries.map((row) => row.uiId)));
              setRowSelection({});
            }}
          >
            {t("global.delete")}
          </Button>
        </Stack>
      );
    },
    renderToolbarInternalActions: ({ table }) => (
      <>
        <MRT_ToggleGlobalFilterButton table={table} />
        <MRT_ToggleFiltersButton table={table} />
      </>
    ),
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
            flexWrap: "nowrap",
          },
        },
      },
    },
    muiTablePaperProps: {
      sx: { display: "flex", flexDirection: "column", flex: "1 1 auto", minHeight: 0 },
    },
    muiTableContainerProps: { sx: { flex: 1, overflow: "auto" } },
    ...getTableOptionsForAlign("center"),
    ...getDarkModeFixStyles(isDarkMode),
  });

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: 1, overflow: "auto" }}>
      <MaterialReactTable table={table} />
      {validationErrors.length > 0 && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          {t("study.modeling.reserves.symmetries.validationError", {
            count: validationErrors.length,
          })}
        </Alert>
      )}
      <Box
        sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 1, mt: 1.5 }}
      >
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          loading={isSaving}
          loadingPosition="start"
          disabled={readOnly || !canSave || isSaving || validationErrors.length > 0}
          onClick={onSave}
        >
          {t("global.save")}
        </Button>
        <Tooltip title={t("global.undo")}>
          <span>
            <IconButton onClick={onUndo} disabled={readOnly || !canUndo || isSaving}>
              <UndoIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Tooltip title={t("global.redo")}>
          <span>
            <IconButton onClick={onRedo} disabled={readOnly || !canRedo || isSaving}>
              <RedoIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
    </Box>
  );
}

export default SymmetriesTable;
