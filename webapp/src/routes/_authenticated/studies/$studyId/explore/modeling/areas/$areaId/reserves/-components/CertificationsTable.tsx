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
import { Box, Chip, Stack, Tooltip } from "@mui/material";
import {
  createMRTColumnHelper,
  MaterialReactTable,
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
        Cell: ({ renderedCellValue, row }) => {
          if (readOnly) {
            return renderedCellValue;
          }

          return (
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
          );
        },
        ...getTableOptionsForAlign("left"),
      }),
      columnHelper.accessor((row) => (row.kind === "reserve" ? row.reserve.type : null), {
        id: "type",
        header: t("global.type"),
        size: 60,
        Cell: ({ cell }) => {
          const type = cell.getValue();

          return (
            type && (
              <Chip
                label={type}
                size="small"
                color={type === "up" ? "success" : "warning"}
                variant="outlined"
                sx={{ borderRadius: 1, textTransform: "uppercase" }}
              />
            )
          );
        },
      }),
      columnHelper.accessor((row) => (row.kind === "reserve" ? row.subRows.length : null), {
        id: "certifiedClusters",
        header: t("study.modeling.reserves.certifications.certifiedClusters"),
        size: 60,
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
            <Stack direction="row" gap={0.5} alignItems="center" justifyContent="flex-end">
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
    muiTablePaperProps: { sx: { display: "flex", flexDirection: "column" } }, // Allow to have scroll
    ...getTableOptionsForAlign("right"),
    ...getDarkModeFixStyles(isDarkMode),
  });

  return <MaterialReactTable table={table} />;
}

export default CertificationsTable;
