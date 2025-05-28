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

import { useState, useMemo, useEffect } from "react";
import { Box, Drawer, Divider, IconButton, Tooltip, Typography, Paper } from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import { useTranslation } from "react-i18next";

import { useMatrixContext } from "../../context/MatrixContext";
import type { MatrixFilterProps } from "./types";
import {
  DRAWER_STYLES,
  COMPONENT_DIMENSIONS,
  DESIGN_TOKENS,
  LAYOUT_SPACING,
  PREVIEW_STYLES,
} from "./styles";
import { getMatrixDimensions } from "./utils";
import ColumnFilter from "./ColumnFilter";
import MultiRowFilter from "./MultiRowFilter";
import Operations from "./Operations";
import SelectionSummary from "./SelectionSummary";
import { useFilteredData } from "./hooks/useFilteredData";
import { useMatrixFilter } from "./hooks/useMatrixFilter";
import DrawerHeader from "./components/DrawerHeader";
import FilterControls from "./components/FilterControls";
import FilterSummaryChips from "./components/FilterSummaryChips";

function MatrixFilter({ dateTime, isTimeSeries, timeFrequency }: MatrixFilterProps) {
  const { t } = useTranslation();
  const { currentState, filterPreview, setFilterPreview } = useMatrixContext();
  const [open, setOpen] = useState(false);

  const { rowCount, columnCount } = useMemo(
    () => getMatrixDimensions(currentState.data),
    [currentState.data],
  );

  const { filter, setFilter, toggleFilter, togglePreviewMode, resetFilters, applyOperation } =
    useMatrixFilter({
      rowCount,
      columnCount,
      timeFrequency,
    });

  const currentFilteredData = useFilteredData({
    filter,
    dateTime,
    isTimeSeries,
    timeFrequency,
    rowCount,
    columnCount,
  });

  // TODO: when activating filters preview mode is on, and with the list filter type
  // that is combined with the = operator the filteredData is empty, and the following log keeps logging infinite times
  console.log("currentFilteredData", currentFilteredData);

  // Update the filter preview when filter criteria changes
  useEffect(() => {
    if (filter.active) {
      setFilterPreview({
        ...filterPreview,
        criteria: currentFilteredData,
      });
    }
  }, [currentFilteredData, filter.active, filterPreview, setFilterPreview]);

  const toggleDrawer = () => {
    requestAnimationFrame(() => {
      setOpen((prev) => !prev);
    });
  };

  return (
    <>
      <Tooltip title={t("matrix.filter.filterData")}>
        <IconButton onClick={toggleDrawer} color={filter.active ? "primary" : "default"}>
          <FilterListIcon />
        </IconButton>
      </Tooltip>

      <Drawer
        anchor="right"
        open={open}
        onClose={toggleDrawer}
        keepMounted
        PaperProps={{
          sx: DRAWER_STYLES.paper,
        }}
        transitionDuration={COMPONENT_DIMENSIONS.drawer.transitionDuration}
      >
        <DrawerHeader onResetFilters={resetFilters} onClose={toggleDrawer} />

        <FilterControls
          isFilterActive={filter.active}
          isPreviewActive={filterPreview.active}
          onToggleFilter={toggleFilter}
          onTogglePreview={() => togglePreviewMode(currentFilteredData)}
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
            onApplyOperation={() => applyOperation(currentFilteredData)}
          />
        </Box>

        <Box
          sx={{
            mt: DESIGN_TOKENS.spacing.lg,
          }}
        >
          <SelectionSummary filteredData={currentFilteredData} previewMode={filterPreview.active} />
        </Box>
      </Drawer>
    </>
  );
}

export default MatrixFilter;
