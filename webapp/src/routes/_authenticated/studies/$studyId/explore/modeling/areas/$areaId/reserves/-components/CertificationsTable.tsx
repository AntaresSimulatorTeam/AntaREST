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
import type {
  CertificationProductionType,
  Reserve,
  ReserveCertification,
} from "@/services/api/studies/areas/reserves/types";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, Chip, Stack, Tooltip, Typography } from "@mui/material";
import {
  createMRTColumnHelper,
  MaterialReactTable,
  MRT_ExpandButton,
  MRT_ToggleFiltersButton,
  MRT_ToggleGlobalFilterButton,
  useMaterialReactTable,
} from "material-react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

export interface ClusterRow {
  kind: "cluster";
  id: string;
  name: string;
  enabled: boolean;
  productionType: CertificationProductionType;
  reserveId: Reserve["id"];
  clusterId: string;
  certification: ReserveCertification;
}

export interface ReserveRow {
  kind: "reserve";
  id: string;
  name: string;
  reserve: Reserve;
  subRows: ClusterRow[];
}

export type CertificationsTableRow = ReserveRow | ClusterRow;

interface Props {
  rows: ReserveRow[];
  readOnly?: boolean;
  isLoading?: boolean;
  onReserveClick: (row: ReserveRow) => void;
  onClusterClick: (row: ClusterRow) => void;
}

const columnHelper = createMRTColumnHelper<CertificationsTableRow>();

const clickableNameStyles = {
  display: "inline",
  cursor: "pointer",
  "&:hover": {
    color: "primary.main",
    textDecoration: "underline",
  },
};

// Displays reserves as parent rows and their certified clusters as expandable
// sub-rows. Clicking a reserve name opens the cluster selection drawer, clicking
// a cluster name opens the certification parameters drawer.
function CertificationsTable({ rows, readOnly, isLoading, onReserveClick, onClusterClick }: Props) {
  const { t } = useTranslation();
  const { isDarkMode } = useThemeColorScheme();

  const columns = useMemo(
    () => [
      columnHelper.accessor("name", {
        header: t("global.name"),
        size: 120,
        Cell: ({ renderedCellValue, row, staticRowIndex, table }) => (
          <Stack direction="row" alignItems="center" gap={0.5}>
            {/* The default expand column is hidden (see `columnVisibility`):
                the button is rendered here so its depth-based margin indents
                sub-rows and content stays flush with the table's left edge. */}
            <MRT_ExpandButton row={row} staticRowIndex={staticRowIndex} table={table} />
            {readOnly ? (
              renderedCellValue
            ) : (
              <Box
                sx={clickableNameStyles}
                onClick={() =>
                  row.original.kind === "reserve"
                    ? onReserveClick(row.original)
                    : onClusterClick(row.original)
                }
              >
                {renderedCellValue}
              </Box>
            )}
            {row.original.kind === "reserve" && (
              <Tooltip title={t("study.modeling.reserves.certifications.certifiedClusters")}>
                <Typography variant="caption" color="text.secondary">
                  ({row.original.subRows.length})
                </Typography>
              </Tooltip>
            )}
          </Stack>
        ),
        ...getTableOptionsForAlign("left"),
      }),
      columnHelper.accessor((row) => (row.kind === "cluster" ? row.enabled : null), {
        id: "enabled",
        header: t("study.modeling.reserves.certifications.field.enabled"),
        size: 80,
        Cell: ({ cell }) => {
          const value = cell.getValue();

          if (value === null) {
            return null;
          }

          return (
            <Chip
              label={value ? t("button.yes") : t("button.no")}
              color={value ? "success" : "error"}
              sx={{ minWidth: 40 }}
            />
          );
        },
      }),
      columnHelper.accessor(
        (row) => (row.kind === "cluster" ? row.certification.participationCost : null),
        {
          id: "participationCost",
          header: t("study.modeling.reserves.certifications.field.participationCost"),
          size: 80,
        },
      ),
      columnHelper.accessor(
        (row) => (row.kind === "cluster" ? row.certification.participationCostOff : null),
        {
          id: "participationCostOff",
          header: t("study.modeling.reserves.certifications.field.participationCostOff"),
          size: 80,
        },
      ),
      columnHelper.accessor((row) => (row.kind === "cluster" ? row.certification.maxPower : null), {
        id: "maxPower",
        header: t("study.modeling.reserves.certifications.field.maxPower"),
        size: 80,
        Cell: ({ cell }) => {
          const value = cell.getValue();

          if (value === null) {
            return null;
          }

          // A max power of 0 means the certification has no effect: prompt the
          // user to fill in the parameters of a newly selected cluster.
          return (
            <Stack gap={0.5} justifyContent="flex-end">
              {value === 0 && (
                <Tooltip title={t("study.modeling.reserves.certifications.incomplete")}>
                  <WarningAmberIcon color="warning" sx={{ fontSize: 16 }} />
                </Tooltip>
              )}
              {value}
            </Stack>
          );
        },
      }),
      columnHelper.accessor(
        (row) => (row.kind === "cluster" ? row.certification.maxPowerOff : null),
        {
          id: "maxPowerOff",
          header: t("study.modeling.reserves.certifications.field.maxPowerOff"),
          size: 80,
        },
      ),
    ],
    [t, readOnly, onReserveClick, onClusterClick],
  );

  const table = useMaterialReactTable({
    data: rows,
    columns,
    getRowId: (row) => row.id,
    getSubRows: (row) => (row.kind === "reserve" ? row.subRows : undefined),
    enableExpanding: true,
    filterFromLeafRows: true,
    initialState: {
      density: "compact",
      expanded: true,
      columnVisibility: { "mrt-row-expand": false },
    },
    state: { isLoading },
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    positionToolbarDropZone: "none",
    // Toolbars
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
            flexWrap: "nowrap", // Prevent the search field to be wrapped
          },
        },
      },
    },
    // Styles
    // `height: 1` bounds the Paper to its scrollable parent panel so
    // `muiTableContainerProps` below can scroll the rows internally,
    // keeping the toolbar and sticky header always in view.
    muiTablePaperProps: { sx: { display: "flex", flexDirection: "column", height: 1 } },
    muiTableContainerProps: { sx: { flex: 1, overflow: "auto" } },
    ...getTableOptionsForAlign("right"),
    ...getDarkModeFixStyles(isDarkMode),
  });

  return <MaterialReactTable table={table} />;
}

export default CertificationsTable;
