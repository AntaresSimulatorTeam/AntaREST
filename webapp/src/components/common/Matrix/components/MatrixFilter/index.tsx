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

import { useState, useMemo } from "react";
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
import { useUpdateEffect } from "react-use";

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

  const togglePreviewMode = () => {
    setFilterPreview({
      active: !filterPreview.active,
      criteria: filteredData,
    });
  };

  // Update the filter preview when filter criteria changes
  useUpdateEffect(() => {
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

          {/* Preview toggle button */}
          {filter.active && (
            <Tooltip
              title={t(
                filterPreview.active
                  ? "matrix.filter.preview.active"
                  : "matrix.filter.preview.inactive",
              )}
            >
              <Button
                variant="outlined"
                color={filterPreview.active ? "info" : "inherit"}
                onClick={togglePreviewMode}
                sx={{
                  minWidth: "unset",
                  width: "42px",
                  height: "36px",
                  borderRadius: 1.5,
                  ...(filterPreview.active && {
                    borderWidth: 1,
                    backgroundColor: "rgba(33, 150, 243, 0.08)",
                  }),
                }}
              >
                {filterPreview.active ? (
                  <VisibilityIcon fontSize="small" />
                ) : (
                  <VisibilityOffIcon fontSize="small" />
                )}
              </Button>
            </Tooltip>
          )}
        </Box>

        <Divider sx={{ mb: 2 }} />

        {filter.active && (
          <Box sx={{ mb: 2 }}>
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                backgroundColor: "background.paper",
                position: "relative",
                ...(filterPreview.active && {
                  boxShadow: "0 0 0 1px rgba(33, 150, 243, 0.2)",
                  borderColor: "rgba(33, 150, 243, 0.3)",
                }),
              }}
            >
              {filterPreview.active && (
                <Box
                  sx={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "2px",
                    height: "100%",
                    bgcolor: "info.main",
                    opacity: 0.7,
                  }}
                />
              )}
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
                          sx={{
                            m: 0.5,
                            ...(filterPreview.active && {
                              borderColor: "info.main",
                              color: "info.main",
                              borderWidth: 1,
                            }),
                          }}
                        />
                      )}
                      {rowFilterTexts.map((text, index) => (
                        <Chip
                          key={`row-filter-${index}-${filter.rowsFilters[index]?.id || crypto.randomUUID()}`}
                          label={text}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{
                            m: 0.5,
                            ...(filterPreview.active && {
                              borderColor: "info.main",
                              color: "info.main",
                              borderWidth: 1,
                            }),
                          }}
                        />
                      ))}
                    </>
                  );
                })()}
              </Stack>
            </Paper>
          </Box>
        )}

        <ColumnFilter
          filter={filter}
          setFilter={setFilter}
          columnCount={currentState.data[0]?.length || 0}
        />

        <MultiRowFilter
          filter={filter}
          setFilter={setFilter}
          dateTime={dateTime}
          isTimeSeries={isTimeSeries}
          timeFrequency={timeFrequency}
        />

        <Operations filter={filter} setFilter={setFilter} onApplyOperation={applyOperation} />

        <Box sx={{ position: "relative" }}>
          {filterPreview.active && (
            <Box
              sx={{
                position: "absolute",
                top: 8,
                right: 8,
                display: "flex",
                alignItems: "center",
                color: "info.dark",
                py: 0.5,
                px: 1,
                borderRadius: 1,
                fontSize: "0.75rem",
                bgcolor: "rgba(33, 150, 243, 0.07)",
                border: "1px solid rgba(33, 150, 243, 0.15)",
                zIndex: 1,
              }}
            >
              <VisibilityIcon sx={{ fontSize: 14, mr: 0.5, opacity: 0.7 }} />
              {t("matrix.filter.previewMode")}
            </Box>
          )}
          <SelectionSummary filteredData={filteredData} previewMode={filterPreview.active} />
        </Box>
      </Drawer>
    </>
  );
}

export default MatrixFilter;
