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

import CloseIcon from "@mui/icons-material/Close";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import FilterListIcon from "@mui/icons-material/FilterList";
import { Box, Divider, Drawer, IconButton, Tooltip } from "@mui/material";
import { forwardRef, useCallback, useImperativeHandle, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import { useMatrixContext } from "../../context/MatrixContext";
import ColumnFilter from "./ColumnFilter";
import FilterControls from "./components/FilterControls";
import { useFilteredData } from "./hooks/useFilteredData";
import { useMatrixFilter } from "./hooks/useMatrixFilter";
import MultiRowFilter from "./MultiRowFilter";
import Operations from "./Operations";
import SelectionSummary from "./SelectionSummary";
import { COMPONENT_DIMENSIONS, DESIGN_TOKENS, DRAWER_STYLES } from "./styles";
import type { MatrixFilterProps } from "./types";
import { extractDatesInfo, getMatrixDimensions } from "./utils";

export interface MatrixFilterHandle {
  toggle: () => void;
}

function MatrixFilter(
  { dateTime, isTimeSeries, timeFrequency, readOnly }: MatrixFilterProps,
  ref: React.ForwardedRef<MatrixFilterHandle>,
) {
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

  const datesInfo = useMemo(() => {
    if (!dateTime || !isTimeSeries || dateTime.values.length === 0) {
      return [];
    }
    return extractDatesInfo(dateTime.values);
  }, [dateTime, isTimeSeries]);

  // Filtered data based on current filter settings
  const currentFilteredData = useFilteredData({
    filter,
    datesInfo,
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

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDrawerToggle = useCallback(() => {
    setIsDrawerOpen((prev) => !prev);
  }, []);

  const handleFilterToggle = useCallback(() => {
    toggleFilter();
  }, [toggleFilter]);

  const handleApplyOperation = useCallback(() => {
    applyOperation(currentFilteredData);
  }, [applyOperation, currentFilteredData]);

  // Expose toggle functionality via ref
  useImperativeHandle(
    ref,
    () => ({
      toggle: handleDrawerToggle,
    }),
    [handleDrawerToggle],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
        keepMounted // Makes the opening/closing smoother
        // hideBackdrop={true} removes the backdrop DOM element entirely,
        // eliminating the click target that triggers onClose.
        // Using transparent backdrop preserves the invisible click target
        // for pointer events while removing the visual overlay.
        slotProps={{
          backdrop: {
            sx: {
              backgroundColor: "transparent",
            },
          },
        }}
        PaperProps={{
          sx: DRAWER_STYLES.paper,
        }}
        transitionDuration={COMPONENT_DIMENSIONS.drawer.transitionDuration}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            mb: DESIGN_TOKENS.spacing.sm,
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

        <Box sx={{ mb: DESIGN_TOKENS.spacing.sm }}>
          <SelectionSummary filteredData={currentFilteredData} />
        </Box>

        <Divider sx={{ mb: DESIGN_TOKENS.spacing.sm, flexShrink: 0 }} />

        <Box sx={DRAWER_STYLES.scrollableContent}>
          <ColumnFilter filter={filter} setFilter={setFilter} columnCount={columnCount} />

          <MultiRowFilter
            filter={filter}
            setFilter={setFilter}
            datesInfo={datesInfo}
            timeFrequency={timeFrequency}
          />

          {!readOnly && (
            <Operations
              filter={filter}
              setFilter={setFilter}
              onApplyOperation={handleApplyOperation}
            />
          )}
        </Box>
      </Drawer>
    </>
  );
}

export default forwardRef(MatrixFilter);
