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
import {
  Box,
  Button,
  Drawer,
  Divider,
  IconButton,
  Stack,
  Chip,
  Tooltip,
  Typography,
  Paper,
} from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import CloseIcon from "@mui/icons-material/Close";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { useTranslation } from "react-i18next";
import { useMatrixContext } from "../../context/MatrixContext";
import { Operation } from "../../shared/constants";
import { calculateMatrixAggregates } from "../../shared/utils";
import type { FilterState, FilterCriteria, MatrixFilterProps } from "./types";
import { FILTER_TYPES, getDefaultFilterState } from "./constants";
import ColumnFilter from "./ColumnFilter";
import MultiRowFilter from "./MultiRowFilter";
import Operations from "./Operations";
import SelectionSummary from "./SelectionSummary";
import { processRowFilters } from "./utils";

function MatrixFilter({ dateTime, isTimeSeries, timeFrequency }: MatrixFilterProps) {
  const { t } = useTranslation();
  const { currentState, setMatrixData, aggregateTypes, setFilterPreview, filterPreview } =
    useMatrixContext();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<FilterState>(
    getDefaultFilterState(
      currentState.data.length,
      currentState.data[0]?.length || 0,
      timeFrequency,
    ),
  );

  // Calculate the filtered data based on current filter settings
  const filteredData = useMemo((): FilterCriteria => {
    if (!filter.active) {
      // Return all rows and columns when filter is not active
      return {
        columnsIndices: Array.from({ length: currentState.data[0]?.length || 0 }, (_, i) => i),
        rowsIndices: Array.from({ length: currentState.data.length || 0 }, (_, i) => i),
      };
    }

    // Filter columns
    let columnsIndices: number[] = [];
    const totalColumns = currentState.data[0]?.length || 0;

    if (filter.columnsFilter.type === FILTER_TYPES.RANGE && filter.columnsFilter.range) {
      const { min, max } = filter.columnsFilter.range;
      columnsIndices = Array.from({ length: totalColumns }, (_, i) => i + 1)
        .filter((idx) => idx >= min && idx <= max)
        .map((idx) => idx - 1); // Convert to 0-based index
    } else if (filter.columnsFilter.type === FILTER_TYPES.LIST && filter.columnsFilter.list) {
      columnsIndices = filter.columnsFilter.list
        .map((idx) => idx - 1)
        .filter((idx) => idx >= 0 && idx < totalColumns);
    }

    // Process multiple row filters and get combined indices
    const rowsIndices: number[] = processRowFilters(
      filter,
      dateTime,
      isTimeSeries,
      timeFrequency,
      currentState.data.length,
    );

    return { columnsIndices, rowsIndices };
  }, [currentState.data, filter, dateTime, isTimeSeries, timeFrequency]);

  // Enable preview mode, allowing users to preview the filtered data before applying operations on it.
  const togglePreviewMode = () => {
    setFilterPreview({
      active: !filterPreview.active,
      criteria: filteredData,
    });
  };

  // Update the filter preview when filter criteria changes
  useEffect(() => {
    if (filter.active) {
      setFilterPreview({
        ...filterPreview,
        criteria: filteredData,
      });
    } else {
      // Deactivate preview when filter is deactivated
      setFilterPreview({
        active: false,
        criteria: filteredData,
      });
    }
  }, [filteredData, filter.active, setFilterPreview, filterPreview]);

  const applyOperation = () => {
    if (!filter.active || currentState.data.length === 0) {
      return;
    }

    const { columnsIndices, rowsIndices } = filteredData;
    const { type: opType, value } = filter.operation;

    // Create a deep copy of the matrix data
    const newData = currentState.data.map((row) => [...row]);

    // Apply the operation to each filtered cell
    for (const rowIdx of rowsIndices) {
      for (const colIdx of columnsIndices) {
        const currentValue = newData[rowIdx][colIdx];

        switch (opType) {
          case Operation.Eq:
            newData[rowIdx][colIdx] = value;
            break;
          case Operation.Add:
            newData[rowIdx][colIdx] = currentValue + value;
            break;
          case Operation.Sub:
            newData[rowIdx][colIdx] = currentValue - value;
            break;
          case Operation.Mul:
            newData[rowIdx][colIdx] = currentValue * value;
            break;
          case Operation.Div:
            // Prevent division by zero
            if (value !== 0) {
              newData[rowIdx][colIdx] = currentValue / value;
            }
            break;
          case Operation.Abs:
            newData[rowIdx][colIdx] = Math.abs(currentValue);
            break;
        }
      }
    }

    // Update the matrix data
    setMatrixData({
      data: newData,
      aggregates: calculateMatrixAggregates({ matrix: newData, types: aggregateTypes }),
    });
  };

  const resetFilters = () => {
    setFilter(
      getDefaultFilterState(
        currentState.data.length,
        currentState.data[0]?.length || 0,
        timeFrequency,
      ),
    );

    setFilterPreview({
      active: false,
      criteria: {
        columnsIndices: Array.from({ length: currentState.data[0]?.length || 0 }, (_, i) => i),
        rowsIndices: Array.from({ length: currentState.data.length || 0 }, (_, i) => i),
      },
    });
  };

  const toggleDrawer = () => {
    setOpen(!open);
  };

  const toggleFilter = () => {
    setFilter({ ...filter, active: !filter.active });
  };

  const getFilterSummary = () => {
    if (!filter.active) {
      return { columnFilterText: "", rowFilterTexts: [] };
    }

    const { columnsFilter, rowsFilters } = filter;
    let columnFilterText = "";
    const rowFilterTexts: string[] = [];

    // Column filter summary
    if (columnsFilter.type === FILTER_TYPES.RANGE && columnsFilter.range) {
      columnFilterText = `${t("matrix.filter.columns")}: ${columnsFilter.range.min} - ${columnsFilter.range.max}`;
    } else if (columnsFilter.type === FILTER_TYPES.LIST && columnsFilter.list) {
      columnFilterText = `${t("matrix.filter.columns")}: [${columnsFilter.list.join(", ")}]`;
    }

    // Row filters summary (multiple)
    for (const rowFilter of rowsFilters) {
      const indexType = t(`matrix.filter.indexing.${rowFilter.indexingType}`);
      if (rowFilter.type === FILTER_TYPES.RANGE && rowFilter.range) {
        rowFilterTexts.push(
          `${t("matrix.filter.rows")} (${indexType}): ${rowFilter.range.min} - ${rowFilter.range.max}`,
        );
      } else if (rowFilter.type === FILTER_TYPES.LIST && rowFilter.list) {
        rowFilterTexts.push(
          `${t("matrix.filter.rows")} (${indexType}): [${rowFilter.list.join(", ")}]`,
        );
      }
    }

    return { columnFilterText, rowFilterTexts };
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
        PaperProps={{
          sx: { p: 2, maxWidth: "400px" },
        }}
      >
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h6">{t("matrix.filter.title")}</Typography>
          <Box>
            <Tooltip title={t("matrix.filter.resetFilters")}>
              <IconButton onClick={resetFilters} size="small">
                <FilterAltOffIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={t("matrix.filter.close")}>
              <IconButton onClick={toggleDrawer} size="small">
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Side-by-side buttons container */}
        <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
          {/* Main filter toggle button */}
          <Button
            variant={filter.active ? "contained" : "outlined"}
            color={filter.active ? "primary" : "inherit"}
            onClick={toggleFilter}
            startIcon={<FilterListIcon />}
            sx={{ flex: 1 }}
          >
            {filter.active ? t("matrix.filter.active") : t("matrix.filter.inactive")}
          </Button>

          {/* Preview toggle button - smaller and side-by-side */}
          {filter.active && (
            <Tooltip
              title={t(filterPreview.active ? "matrix.preview.active" : "matrix.preview.inactive")}
            >
              <Button
                variant={filterPreview.active ? "contained" : "outlined"}
                color={filterPreview.active ? "secondary" : "inherit"}
                onClick={togglePreviewMode}
                sx={{ minWidth: "unset", width: "48px" }}
              >
                {filterPreview.active ? <VisibilityIcon /> : <VisibilityOffIcon />}
              </Button>
            </Tooltip>
          )}
        </Box>

        <Divider sx={{ mb: 2 }} />

        {filter.active && (
          <Box sx={{ mb: 2 }}>
            <Paper variant="outlined" sx={{ p: 1.5, backgroundColor: "background.paper" }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {t("matrix.filter.activeFilters")}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {(() => {
                  const { columnFilterText, rowFilterTexts } = getFilterSummary();
                  return (
                    <>
                      {columnFilterText && (
                        <Chip
                          label={columnFilterText}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ m: 0.5 }}
                        />
                      )}
                      {rowFilterTexts.map((text) => (
                        <Chip
                          key={`row-filter-${text}`}
                          label={text}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ m: 0.5 }}
                        />
                      ))}
                    </>
                  );
                })()}
              </Stack>
            </Paper>
          </Box>
        )}

        <ColumnFilter filter={filter} setFilter={setFilter} />

        <MultiRowFilter
          filter={filter}
          setFilter={setFilter}
          dateTime={dateTime}
          isTimeSeries={isTimeSeries}
          timeFrequency={timeFrequency}
        />

        <Operations filter={filter} setFilter={setFilter} onApplyOperation={applyOperation} />

        <SelectionSummary filteredData={filteredData} />
      </Drawer>
    </>
  );
}

export default MatrixFilter;
