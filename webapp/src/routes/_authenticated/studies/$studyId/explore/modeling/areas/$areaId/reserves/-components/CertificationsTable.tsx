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
  ProductionType,
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
import { PRODUCTION_TYPES } from "../-productionTypes";

export interface AssetRow {
  kind: "asset";
  id: string;
  name: string;
  // Omitted for assets without an activation state (hydro).
  enabled?: boolean;
  productionType: ProductionType;
  reserveId: Reserve["id"];
  assetId: string;
  certification: ReserveCertification;
}

export interface ReserveRow {
  kind: "reserve";
  id: string;
  name: string;
  reserve: Reserve;
  subRows: AssetRow[];
}

export type CertificationsTableRow = ReserveRow | AssetRow;

interface Props {
  rows: ReserveRow[];
  productionType: ProductionType;
  // Rendered at the start of the table toolbar (e.g. the production type select).
  toolbarActions?: React.ReactNode;
  readOnly?: boolean;
  isLoading?: boolean;
  onReserveClick: (row: ReserveRow) => void;
  onAssetClick: (row: AssetRow) => void;
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

// Certification parameters differ by production type: read them by name.
function getCertificationValue(certification: ReserveCertification, field: string) {
  const values: Record<string, number> = certification;
  return values[field] ?? null;
}

// Displays reserves as parent rows and their certified assets as expandable
// sub-rows, with one column per certification parameter of the production type.
// Clicking a reserve name opens the asset selection drawer, clicking an asset
// name opens the certification parameters drawer.
function CertificationsTable({
  rows,
  productionType,
  toolbarActions,
  readOnly,
  isLoading,
  onReserveClick,
  onAssetClick,
}: Props) {
  const { t } = useTranslation();
  const { isDarkMode } = useThemeColorScheme();
  const {
    assetsHaveActivationState,
    certificationFields,
    isCertificationIncomplete,
    incompleteLabelKey,
  } = PRODUCTION_TYPES[productionType];

  const columns = useMemo(
    () => [
      columnHelper.accessor("name", {
        header: t("global.name"),
        size: 120,
        Cell: ({ renderedCellValue, row, staticRowIndex, table }) => (
          <Stack direction="row" alignItems="center" gap={0.5}>
            <MRT_ExpandButton row={row} staticRowIndex={staticRowIndex} table={table} />
            {readOnly ? (
              renderedCellValue
            ) : (
              <Box
                sx={clickableNameStyles}
                onClick={() =>
                  row.original.kind === "reserve"
                    ? onReserveClick(row.original)
                    : onAssetClick(row.original)
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
            {/* A saved certification with no effect yet: prompt the user to
                fill in the parameters of a newly selected asset. */}
            {row.original.kind === "asset" &&
              isCertificationIncomplete(row.original.certification) && (
                <Tooltip title={t(incompleteLabelKey)}>
                  <WarningAmberIcon color="warning" sx={{ fontSize: 16 }} />
                </Tooltip>
              )}
          </Stack>
        ),
        ...getTableOptionsForAlign("left"),
      }),
      columnHelper.accessor((row) => (row.kind === "asset" ? (row.enabled ?? null) : null), {
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
      ...certificationFields.map((field) =>
        columnHelper.accessor(
          (row) => (row.kind === "asset" ? getCertificationValue(row.certification, field) : null),
          {
            id: field,
            header: t(`study.modeling.reserves.certifications.field.${field}`),
            size: 80,
          },
        ),
      ),
    ],
    [
      t,
      readOnly,
      certificationFields,
      isCertificationIncomplete,
      incompleteLabelKey,
      onReserveClick,
      onAssetClick,
    ],
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
    },
    state: {
      isLoading,
      columnVisibility: { "mrt-row-expand": false, enabled: assetsHaveActivationState },
    },
    enableStickyHeader: true,
    enableColumnDragging: false,
    enableColumnActions: false,
    enableBottomToolbar: false,
    enablePagination: false,
    positionToolbarAlertBanner: "none",
    positionToolbarDropZone: "none",
    // Toolbars
    renderTopToolbarCustomActions: () => toolbarActions,
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
          py: 0.5,
          "> .MuiBox-root": {
            flexWrap: "nowrap", // Prevent the search field to be wrapped
          },
        },
      },
    },
    muiTablePaperProps: { sx: { display: "flex", flexDirection: "column", height: 1 } },
    muiTableContainerProps: { sx: { flex: 1, overflow: "auto" } },
    ...getTableOptionsForAlign("right"),
    ...getDarkModeFixStyles(isDarkMode),
  });

  return <MaterialReactTable table={table} />;
}

export default CertificationsTable;
