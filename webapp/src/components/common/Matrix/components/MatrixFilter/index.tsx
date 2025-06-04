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

import { useState, useMemo, useRef, useCallback } from "react";
import { Box, Drawer, Divider, IconButton, Tooltip, Typography, Paper } from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import { useTranslation } from "react-i18next";
import { useMatrixContext } from "../../context/MatrixContext";
import type { MatrixFilterProps, FilterCriteria } from "./types";
import { useFilteredData } from "./hooks/useFilteredData";
import { useMatrixFilter } from "./hooks/useMatrixFilter";
import { areFilterCriteriaEqual } from "./utils/compareUtils";
import ColumnFilter from "./ColumnFilter";
import MultiRowFilter from "./MultiRowFilter";
import Operations from "./Operations";
import SelectionSummary from "./SelectionSummary";
import DrawerHeader from "./components/DrawerHeader";
import FilterControls from "./components/FilterControls";
import FilterSummaryChips from "./components/FilterSummaryChips";
import { getMatrixDimensions } from "./utils";
import {
  DRAWER_STYLES,
  COMPONENT_DIMENSIONS,
  DESIGN_TOKENS,
  LAYOUT_SPACING,
  PREVIEW_STYLES,
} from "./styles";
import { useUpdateEffect } from "react-use";

function MatrixFilter({ dateTime, isTimeSeries, timeFrequency }: MatrixFilterProps) {
  const { t } = useTranslation();
  const { currentState, filterPreview, setFilterPreview } = useMatrixContext();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const prevFilteredDataRef = useRef<FilterCriteria | null>(null);

  // Matrix dimensions
  const { rowCount, columnCount } = useMemo(
    () => getMatrixDimensions(currentState.data),
    [currentState.data],
  );

  // Filter state and operations
  const { filter, setFilter, toggleFilter, togglePreviewMode, resetFilters, applyOperation } =
    useMatrixFilter({
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
    if (!filter.active) {
      return;
    }

    const hasChanged = !areFilterCriteriaEqual(prevFilteredDataRef.current, currentFilteredData);

    if (hasChanged) {
      prevFilteredDataRef.current = {
        columnsIndices: [...currentFilteredData.columnsIndices],
        rowsIndices: [...currentFilteredData.rowsIndices],
      };

      setFilterPreview({
        active: filterPreview.active,
        criteria: currentFilteredData,
      });
    }
  }, [filter.active, currentFilteredData, setFilterPreview, filterPreview.active]);

  const handleDrawerToggle = useCallback(() => {
    requestAnimationFrame(() => {
      setIsDrawerOpen((prev) => !prev);
    });
  }, []);

  const handleFilterToggle = useCallback(() => {
    const willBeActive = !filter.active;
    toggleFilter();

    if (willBeActive && !filterPreview.active) {
      setFilterPreview({
        active: true,
        criteria: currentFilteredData,
      });
    } else if (!willBeActive) {
      setFilterPreview({
        active: false,
        // TODO remove indices generation logic as it seems unnecessary
        criteria: {
          columnsIndices: Array.from({ length: columnCount }, (_, i) => i),
          rowsIndices: Array.from({ length: rowCount }, (_, i) => i),
        },
      });
    }
  }, [
    filter.active,
    filterPreview.active,
    toggleFilter,
    setFilterPreview,
    currentFilteredData,
    columnCount,
    rowCount,
  ]);

  const handleApplyOperation = useCallback(() => {
    applyOperation(currentFilteredData);
  }, [applyOperation, currentFilteredData]);

  const handleTogglePreview = useCallback(() => {
    togglePreviewMode(currentFilteredData);
  }, [togglePreviewMode, currentFilteredData]);

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
        <DrawerHeader onResetFilters={resetFilters} onClose={handleDrawerToggle} />

        <FilterControls
          isFilterActive={filter.active}
          isPreviewActive={filterPreview.active}
          onToggleFilter={handleFilterToggle}
          onTogglePreview={handleTogglePreview}
        />

        <Divider sx={{ mb: DESIGN_TOKENS.spacing.xl, flexShrink: 0 }} />

        {filter.active && (
          <Box sx={LAYOUT_SPACING.section}>
            <Paper
              variant="outlined"
              sx={{
                p: DESIGN_TOKENS.spacing.md,
                ...(filterPreview.active && PREVIEW_STYLES.container),
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  fontSize: DESIGN_TOKENS.fontSize.sm,
                  mb: DESIGN_TOKENS.spacing.xs,
                  display: "block",
                }}
              >
                {t("matrix.filter.activeFilters")}
              </Typography>
              <FilterSummaryChips filter={filter} isPreviewActive={filterPreview.active} />
            </Paper>
          </Box>
        )}

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
          <SelectionSummary filteredData={currentFilteredData} previewMode={filterPreview.active} />
        </Box>
      </Drawer>
    </>
  );
}

export default MatrixFilter;
