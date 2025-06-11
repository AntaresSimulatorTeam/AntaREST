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

import { useState, useMemo, useCallback } from "react";
import { Box, Drawer, Divider, IconButton, Tooltip } from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import CloseIcon from "@mui/icons-material/Close";
import { useTranslation } from "react-i18next";
import { useMatrixContext } from "../../context/MatrixContext";
import type { MatrixFilterProps } from "./types";
import { useFilteredData } from "./hooks/useFilteredData";
import { useMatrixFilter } from "./hooks/useMatrixFilter";

import ColumnFilter from "./ColumnFilter";
import MultiRowFilter from "./MultiRowFilter";
import Operations from "./Operations";
import SelectionSummary from "./SelectionSummary";
import FilterControls from "./components/FilterControls";
import { getMatrixDimensions } from "./utils";
import { DRAWER_STYLES, COMPONENT_DIMENSIONS, DESIGN_TOKENS } from "./styles";
import { useUpdateEffect } from "react-use";

function MatrixFilter({ dateTime, isTimeSeries, timeFrequency }: MatrixFilterProps) {
  const { t } = useTranslation();
  const { currentState, setFilterPreview } = useMatrixContext();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Matrix dimensions
  const { rowCount, columnCount } = useMemo(
    () => getMatrixDimensions(currentState.data),
    [currentState.data],
  );

  // Filter state and operations
  const { filter, setFilter, toggleFilter, resetFilters, applyOperation } = useMatrixFilter({
    rowCount,
    columnCount,
    timeFrequency,
  });

  // Filtered data based on current filter settings
  const currentFilteredData = useFilteredData({
    filter,
    dateTime,
    isTimeSeries,
    timeFrequency,
    rowCount,
    columnCount,
  });

  // Sync filter preview with filtered data when filter is active
  useUpdateEffect(() => {
    setFilterPreview({
      active: filter.active,
      criteria: filter.active
        ? currentFilteredData
        : {
            columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
            rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
          },
    });
  }, [filter.active, currentFilteredData, setFilterPreview, columnCount, rowCount]);

  const handleDrawerToggle = useCallback(() => {
    setIsDrawerOpen((prev) => !prev);
  }, []);

  const handleFilterToggle = useCallback(() => {
    toggleFilter();
  }, [toggleFilter]);

  const handleApplyOperation = useCallback(() => {
    applyOperation(currentFilteredData);
  }, [applyOperation, currentFilteredData]);

  return (
    <>
      <Tooltip title={t("matrix.filter.filterData")}>
        <IconButton
          onClick={handleDrawerToggle}
          color={filter.active ? "primary" : "default"}
          aria-label={t("matrix.filter.filterData")}
        >
          <FilterListIcon />
        </IconButton>
      </Tooltip>

      <Drawer
        anchor="right"
        open={isDrawerOpen}
        onClose={handleDrawerToggle}
        keepMounted
        PaperProps={{
          sx: DRAWER_STYLES.paper,
        }}
        transitionDuration={COMPONENT_DIMENSIONS.drawer.transitionDuration}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: DESIGN_TOKENS.spacing.xl,
            flexShrink: 0,
          }}
        >
          <FilterControls isFilterActive={filter.active} onToggleFilter={handleFilterToggle} />
          <Box sx={{ display: "flex", gap: DESIGN_TOKENS.spacing.sm }}>
            <Tooltip title={t("matrix.filter.resetFilters")}>
              <IconButton onClick={resetFilters} size="small">
                <FilterAltOffIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t("matrix.filter.close")}>
              <IconButton onClick={handleDrawerToggle} size="small">
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Divider sx={{ mb: DESIGN_TOKENS.spacing.xl, flexShrink: 0 }} />

        <Box sx={DRAWER_STYLES.scrollableContent}>
          <ColumnFilter filter={filter} setFilter={setFilter} columnCount={columnCount} />

          <MultiRowFilter
            filter={filter}
            setFilter={setFilter}
            dateTime={dateTime}
            isTimeSeries={isTimeSeries}
            timeFrequency={timeFrequency}
          />

          <Operations
            filter={filter}
            setFilter={setFilter}
            onApplyOperation={handleApplyOperation}
          />
        </Box>

        <Box sx={{ mt: DESIGN_TOKENS.spacing.lg }}>
          <SelectionSummary filteredData={currentFilteredData} previewMode={filter.active} />
        </Box>
      </Drawer>
    </>
  );
}

export default MatrixFilter;
