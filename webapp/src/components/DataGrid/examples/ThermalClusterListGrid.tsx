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

/**
 * ThermalClusterListGrid
 *
 * Concrete example of a Glide Data Grid table that combines:
 *
 *  ┌─────────────────────────────────────────────────────────────────┐
 *  │  Listing  │  Inline editing  │  Custom cells                    │
 *  │           │                  │  · SelectCell  → group / genTs   │
 *  │           │                  │  · ToggleCell  → enabled/mustRun │
 *  │           │                  │  · ButtonCell  → per-row save    │
 *  └─────────────────────────────────────────────────────────────────┘
 *
 * The component intentionally does NOT depend on DataGridForm so that
 * `customRenderers` can be forwarded to DataGrid freely.  The same
 * undo / redo / dirty-state / submit footer pattern used inside
 * DataGridForm is reproduced here so the UX stays consistent.
 *
 * Usage example (inside a route component):
 *
 * ```tsx
 * const { data: clusters = [] } = usePromise(
 *   () => getThermalClusters(studyId, areaId),
 *   [studyId, areaId],
 * );
 *
 * <ThermalClusterListGrid
 *   clusters={clusters}
 *   onSaveRow={(id, patch) => updateThermalCluster(studyId, areaId, id, patch)}
 *   onSaveAll={(rows) => saveAllThermalClusters(studyId, areaId, rows)}
 * />
 * ```
 */

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import {
  GridCellKind,
  type CustomCell,
  type DataEditorProps,
  type GridColumn,
  type Item,
} from "@glideapps/glide-data-grid";
import RedoIcon from "@mui/icons-material/Redo";
import SaveIcon from "@mui/icons-material/Save";
import UndoIcon from "@mui/icons-material/Undo";
import { Box, Button, Divider, IconButton, Tooltip, Typography } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useUndo from "use-undo";
import DataGrid from "../../DataGrid";
import {
  ALL_CUSTOM_RENDERERS,
  type ButtonCellProps,
  type SelectCellProps,
  type ToggleCellProps,
} from "../customCells";
import {
  THERMAL_GROUPS,
  TS_GENERATION_OPTIONS,
} from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/-utils";

////////////////////////////////////////////////////////////////
// Row type
//
// This is a lightweight subset of the full ThermalCluster type,
// containing only the fields shown in the list table.
////////////////////////////////////////////////////////////////

export interface ThermalClusterRow {
  /** Unique identifier (used as the row key). */
  id: string;
  /** Human-readable name (shown as the frozen row-marker column). */
  name: string;
  group: (typeof THERMAL_GROUPS)[number] | string;
  enabled: boolean;
  mustRun: boolean;
  unitCount: number;
  /** MW */
  nominalCapacity: number;
  /** €/MWh */
  marketBidCost: number;
  genTs: (typeof TS_GENERATION_OPTIONS)[number];
}

////////////////////////////////////////////////////////////////
// Column definitions
//
// "_save" is a virtual column that renders a ButtonCell.
// It does not map to any ThermalClusterRow field.
////////////////////////////////////////////////////////////////

type ColumnId = keyof ThermalClusterRow | "_save";

type ColDef = GridColumn & { id: ColumnId };

const COLUMNS: ColDef[] = [
  { id: "enabled", title: "Enabled", width: 90 },
  { id: "mustRun", title: "Must Run", width: 90 },
  { id: "group", title: "Group", width: 140 },
  { id: "unitCount", title: "Unit Count", width: 100 },
  { id: "nominalCapacity", title: "Nominal Capacity (MW)", width: 190 },
  { id: "marketBidCost", title: "Market Bid (€/MWh)", width: 170 },
  { id: "genTs", title: "TS Generation", width: 165 },
  { id: "_save", title: "", width: 80 },
];

////////////////////////////////////////////////////////////////
// Component props
////////////////////////////////////////////////////////////////

export interface ThermalClusterListGridProps {
  /** Initial list of clusters, already fetched from the API. */
  clusters: ThermalClusterRow[];
  /**
   * Called when the user clicks the per-row "Save" button cell.
   * Receives the cluster id and a partial object containing only
   * the fields that differ from the original row.
   */
  onSaveRow?: (id: string, changes: Partial<ThermalClusterRow>) => Promise<void>;
  /**
   * Called when the user clicks the global "Save" button in the footer.
   * Receives the full current list of rows.
   */
  onSaveAll?: (rows: ThermalClusterRow[]) => Promise<void>;
  /** When true every cell is rendered in read-only mode. */
  readOnly?: boolean;
}

////////////////////////////////////////////////////////////////
// Helpers
////////////////////////////////////////////////////////////////

/**
 * Build a partial diff between two rows (only changed fields).
 *
 * @param original
 * @param updated
 */
function diffRow(
  original: ThermalClusterRow,
  updated: ThermalClusterRow,
): Partial<ThermalClusterRow> {
  return (Object.keys(updated) as Array<keyof ThermalClusterRow>).reduce((acc, key) => {
    if (updated[key] !== original[key]) {
      // TypeScript doesn't narrow the union automatically here
      (acc as Record<string, unknown>)[key] = updated[key];
    }
    return acc;
  }, {} as Partial<ThermalClusterRow>);
}

////////////////////////////////////////////////////////////////
// Component
////////////////////////////////////////////////////////////////

export default function ThermalClusterListGrid({
  clusters: initialClusters,
  onSaveRow,
  onSaveAll,
  readOnly = false,
}: ThermalClusterListGridProps) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  // ── State ──────────────────────────────────────────────────
  const [savedRows, setSavedRows] = useState<ThermalClusterRow[]>(initialClusters);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // useUndo gives us undo/redo over the full rows array at zero cost
  const [{ present: rows }, { set: setRows, undo, redo, canUndo, canRedo }] =
    useUndo(initialClusters);

  // Track which rows are being saved individually (by id)
  const [savingRowIds, setSavingRowIds] = useState<Set<string>>(new Set());

  // Reference comparison — same strategy as DataGridForm
  const isDirty = savedRows !== rows;
  const canSubmit = isDirty && !isSubmitting;

  // ── Column helpers ─────────────────────────────────────────

  const columnIds = useMemo<ColumnId[]>(() => COLUMNS.map((c) => c.id), []);

  const rowNames = useMemo(() => rows.map((r) => r.name), [rows]);

  // ── Per-row save ───────────────────────────────────────────

  /**
   * Save a single row to the API without touching other rows.
   * Fired by the ButtonCell onClick callback.
   *
   * @param rowIndex
   */
  const handleSaveRow = useCallback(
    async (rowIndex: number) => {
      if (!onSaveRow) {
        return;
      }

      const row = rows[rowIndex];
      const original = savedRows.find((r) => r.id === row.id);
      const changes = original ? diffRow(original, row) : row;

      if (Object.keys(changes).length === 0) {
        return; // nothing to save
      }

      setSavingRowIds((prev) => new Set(prev).add(row.id));

      try {
        await onSaveRow(row.id, changes);
        // Patch savedRows so the row is no longer dirty
        setSavedRows((prev) => prev.map((r) => (r.id === row.id ? { ...r, ...changes } : r)));
      } catch (err) {
        enqueueErrorSnackbar(t("form.submit.error"), toError(err));
      } finally {
        setSavingRowIds((prev) => {
          const next = new Set(prev);
          next.delete(row.id);
          return next;
        });
      }
    },
    [rows, savedRows, onSaveRow, enqueueErrorSnackbar, t],
  );

  // ── Global save ────────────────────────────────────────────

  const handleSaveAll = async () => {
    if (!onSaveAll || !canSubmit) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSaveAll(rows);
      setSavedRows(rows);
    } catch (err) {
      enqueueErrorSnackbar(t("form.submit.error"), toError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Cell content ───────────────────────────────────────────

  /**
   * Map a grid location [colIndex, rowIndex] to a GridCell.
   *
   * DataGrid already strips the frozen name column offset before
   * calling this, so colIndex 0 === COLUMNS[0].
   */
  const getCellContent = useCallback<DataEditorProps["getCellContent"]>(
    ([colIndex, rowIndex]: Item) => {
      const row = rows[rowIndex];
      const colId = columnIds[colIndex];

      if (!row || !colId) {
        return {
          kind: GridCellKind.Text,
          data: "",
          displayData: "",
          allowOverlay: false,
          readonly: true,
        };
      }

      // ── ToggleCell ── enabled / mustRun ──────────────────────
      if (colId === "enabled" || colId === "mustRun") {
        return {
          kind: GridCellKind.Custom,
          allowOverlay: false, // toggle is click-only, no overlay needed
          copyData: row[colId] ? "true" : "false",
          data: {
            kind: "toggle-cell",
            value: row[colId] as boolean,
            label: row[colId] ? "Yes" : "No",
            readonly: readOnly,
          } satisfies ToggleCellProps,
        } satisfies CustomCell<ToggleCellProps>;
      }

      // ── SelectCell ── group ──────────────────────────────────
      if (colId === "group") {
        return {
          kind: GridCellKind.Custom,
          allowOverlay: true,
          copyData: row.group,
          data: {
            kind: "select-cell",
            value: row.group,
            options: [...THERMAL_GROUPS],
            readonly: readOnly,
          } satisfies SelectCellProps,
        } satisfies CustomCell<SelectCellProps>;
      }

      // ── SelectCell ── genTs ──────────────────────────────────
      if (colId === "genTs") {
        return {
          kind: GridCellKind.Custom,
          allowOverlay: true,
          copyData: row.genTs,
          data: {
            kind: "select-cell",
            value: row.genTs,
            options: [...TS_GENERATION_OPTIONS],
            readonly: readOnly,
          } satisfies SelectCellProps,
        } satisfies CustomCell<SelectCellProps>;
      }

      // ── ButtonCell ── per-row save ───────────────────────────
      if (colId === "_save") {
        const isSaving = savingRowIds.has(row.id);
        const savedRow = savedRows.find((r) => r.id === row.id);
        const rowIsDirty = savedRow ? Object.keys(diffRow(savedRow, row)).length > 0 : true;

        return {
          kind: GridCellKind.Custom,
          allowOverlay: false,
          copyData: "",
          data: {
            kind: "button-cell",
            label: isSaving ? "…" : "Save",
            icon: isSaving ? undefined : "💾",
            variant: "outlined",
            disabled: readOnly || isSaving || !rowIsDirty,
            // This callback runs inside the renderer's onClick handler.
            // It captures rowIndex from the closure.
            onClick: () => handleSaveRow(rowIndex),
          } satisfies ButtonCellProps,
        } satisfies CustomCell<ButtonCellProps>;
      }

      // ── Number cells ── unitCount / nominalCapacity / marketBidCost ──
      if (colId === "unitCount" || colId === "nominalCapacity" || colId === "marketBidCost") {
        const raw = row[colId] as number;
        return {
          kind: GridCellKind.Number,
          data: raw,
          displayData:
            colId === "unitCount" ? raw.toString() : raw.toFixed(colId === "marketBidCost" ? 2 : 1),
          allowOverlay: !readOnly,
          readonly: readOnly,
          contentAlign: "right",
          thousandSeparator: " ",
        };
      }

      // ── Fallback: plain text ─────────────────────────────────
      const raw = row[colId as keyof ThermalClusterRow];
      const text = raw !== undefined && raw !== null ? String(raw) : "";
      return {
        kind: GridCellKind.Text,
        data: text,
        displayData: text,
        allowOverlay: !readOnly,
        readonly: readOnly,
      };
    },
    [rows, columnIds, savedRows, savingRowIds, readOnly, handleSaveRow],
  );

  // ── Cell editing ───────────────────────────────────────────

  /**
   * Apply a batch of edits to the rows array.
   * Handles Number, Text and Custom (Select / Toggle) cell kinds.
   */
  const handleCellsEdited = useCallback<NonNullable<DataEditorProps["onCellsEdited"]>>(
    (items) => {
      setRows(
        items.reduce((acc, { location: [colIndex, rowIndex], value }) => {
          const colId = columnIds[colIndex];

          // Virtual column — never store its value
          if (!colId || colId === "_save") {
            return acc;
          }

          const current = acc[rowIndex];
          if (!current) {
            return acc;
          }

          // ── Custom cells (Select / Toggle) ──────────────────
          if (value.kind === GridCellKind.Custom) {
            const customData = (value as CustomCell).data as SelectCellProps | ToggleCellProps;

            if (customData.kind === "select-cell" || customData.kind === "toggle-cell") {
              const updated: ThermalClusterRow = {
                ...current,
                [colId]: customData.value,
              };
              const next = [...acc];
              next[rowIndex] = updated;
              return next;
            }
            return acc;
          }

          // ── Number cells ─────────────────────────────────────
          if (value.kind === GridCellKind.Number && value.data !== undefined) {
            // Validate: unitCount must be a positive integer
            if (colId === "unitCount") {
              const int = Math.max(1, Math.round(value.data));
              const next = [...acc];
              next[rowIndex] = { ...current, unitCount: int };
              return next;
            }
            // nominalCapacity and marketBidCost must be >= 0
            if (colId === "nominalCapacity" || colId === "marketBidCost") {
              const clamped = Math.max(0, value.data);
              const next = [...acc];
              next[rowIndex] = { ...current, [colId]: clamped };
              return next;
            }
          }

          // ── Text cells ────────────────────────────────────────
          if (value.kind === GridCellKind.Text && value.data !== undefined) {
            const next = [...acc];
            next[rowIndex] = { ...current, [colId]: value.data };
            return next;
          }

          return acc;
        }, rows),
      );

      // Return true to tell GDG we handled the edits ourselves
      return true;
    },
    [rows, columnIds, setRows],
  );

  // ── JSX ────────────────────────────────────────────────────

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: 1,
        overflow: "hidden",
        gap: 1,
      }}
    >
      {/* ── Dirty indicator ───────────────────────────────── */}
      {isDirty && (
        <Typography variant="caption" color="warning.main" sx={{ pl: 0.5 }}>
          {t("form.unsavedChanges", "You have unsaved changes")}
        </Typography>
      )}

      {/* ── Grid ─────────────────────────────────────────── */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <DataGrid
          // Pass all custom renderers so GDG knows how to draw / edit them
          customRenderers={ALL_CUSTOM_RENDERERS}
          columns={COLUMNS}
          rows={rows.length}
          getCellContent={getCellContent}
          onCellsEdited={handleCellsEdited}
          // Frozen left column shows the cluster name (acts like a row header)
          rowMarkers={{
            kind: "clickable-string",
            getTitle: (index) => rowNames[index] ?? "",
            width: 180,
          }}
          // Allow filling values down/up for numeric and select cells
          fillHandle
          allowedFillDirections="vertical"
          // Allow copy/paste
          getCellsForSelection
          onPaste
          readOnly={readOnly}
        />
      </Box>

      {/* ── Footer: global save + undo / redo ─────────────── */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          pt: 1,
          borderTop: 1,
          borderColor: "divider",
          flexShrink: 0,
        }}
      >
        {!readOnly && onSaveAll && (
          <>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              disabled={!canSubmit}
              loading={isSubmitting}
              loadingPosition="start"
              onClick={handleSaveAll}
            >
              {t("global.save")}
            </Button>
            <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
          </>
        )}

        <Tooltip title={t("global.undo")}>
          <span>
            <IconButton onClick={undo} disabled={!canUndo || isSubmitting} size="small">
              <UndoIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>

        <Tooltip title={t("global.redo")}>
          <span>
            <IconButton onClick={redo} disabled={!canRedo || isSubmitting} size="small">
              <RedoIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
    </Box>
  );
}
