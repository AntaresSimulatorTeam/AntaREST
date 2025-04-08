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
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
  Chip,
  Tooltip,
} from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteIcon from "@mui/icons-material/Delete";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useTranslation } from "react-i18next";
import { useMatrixContext } from "../../context/MatrixContext";
import { Operation } from "../../shared/constants";

const FILTER_TYPES = {
  RANGE: "range",
  MODULO: "modulo",
  LIST: "list",
};

const TIME_INDEXING = {
  DAY_OF_MONTH: "dayOfMonth",
  DAY_OF_YEAR: "dayOfYear",
  DAY_HOUR: "dayHour",
  HOUR_YEAR: "hourYear",
  MONTH: "month",
  WEEK: "week",
  WEEKDAY: "weekday",
};

interface FilterState {
  active: boolean;
  columnsFilter: {
    type: string;
    range?: { min: number; max: number };
    modulo?: { divisor: number; remainder: number };
    list?: number[];
  };
  rowsFilter: {
    indexingType: string;
    type: string;
    range?: { min: number; max: number };
    modulo?: { divisor: number; remainder: number };
    list?: number[];
  };
  operation: {
    type: string;
    value: number;
  };
}

interface FilterCriteria {
  columnsIndices: number[];
  rowsIndices: number[];
}

interface MatrixFilterProps {
  dateTime?: string[];
  isTimeSeries: boolean;
}

function MatrixFilter({ dateTime, isTimeSeries }: MatrixFilterProps) {
  const { t } = useTranslation();
  const { currentState, setMatrixData } = useMatrixContext();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<FilterState>({
    active: false,
    columnsFilter: {
      type: FILTER_TYPES.RANGE,
      range: { min: 1, max: currentState.data[0]?.length || 1 },
    },
    rowsFilter: {
      indexingType: TIME_INDEXING.DAY_OF_MONTH,
      type: FILTER_TYPES.RANGE,
      range: { min: 1, max: currentState.data.length || 1 },
    },
    operation: {
      type: Operation.Eq,
      value: 0,
    },
  });

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
    } else if (filter.columnsFilter.type === FILTER_TYPES.MODULO && filter.columnsFilter.modulo) {
      const { divisor, remainder } = filter.columnsFilter.modulo;
      columnsIndices = Array.from({ length: totalColumns }, (_, i) => i + 1)
        .filter((idx) => idx % divisor === remainder)
        .map((idx) => idx - 1); // Convert to 0-based index
    } else if (filter.columnsFilter.type === FILTER_TYPES.LIST && filter.columnsFilter.list) {
      columnsIndices = filter.columnsFilter.list
        .map((idx) => idx - 1)
        .filter((idx) => idx >= 0 && idx < totalColumns);
    }

    // Filter rows based on time indexing
    let rowsIndices: number[] = [];
    const totalRows = currentState.data.length;

    // Calculate row indices based on the selected indexing type
    const getRowIndices = () => {
      if (!isTimeSeries || !dateTime || dateTime.length === 0) {
        // If not a time series or no dateTime data, use simple row indices
        return Array.from({ length: totalRows }, (_, i) => i + 1);
      }

      // Process date-time data to extract the appropriate indices
      return dateTime.map((date, index) => {
        const dateObj = new Date(date);
        switch (filter.rowsFilter.indexingType) {
          case TIME_INDEXING.DAY_OF_MONTH: {
            return dateObj.getDate();
          }
          case TIME_INDEXING.DAY_OF_YEAR: {
            const start = new Date(dateObj.getFullYear(), 0, 0);
            const diff = dateObj.getTime() - start.getTime();
            return Math.floor(diff / (1000 * 60 * 60 * 24));
          }
          case TIME_INDEXING.DAY_HOUR: {
            return dateObj.getHours() + 1;
          }
          case TIME_INDEXING.HOUR_YEAR: {
            const yearStart = new Date(dateObj.getFullYear(), 0, 0);
            const hourDiff = dateObj.getTime() - yearStart.getTime();
            return Math.floor(hourDiff / (1000 * 60 * 60)) + 1;
          }
          case TIME_INDEXING.MONTH: {
            return dateObj.getMonth() + 1;
          }
          case TIME_INDEXING.WEEK: {
            const startOfYear = new Date(dateObj.getFullYear(), 0, 1);
            const days = Math.floor(
              (dateObj.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000),
            );
            return Math.ceil((days + startOfYear.getDay() + 1) / 7);
          }
          case TIME_INDEXING.WEEKDAY: {
            return dateObj.getDay() === 0 ? 7 : dateObj.getDay(); // 1 (Monday) to 7 (Sunday)
          }
          default: {
            return index + 1;
          }
        }
      });
    };

    const rowTimeIndices = getRowIndices();

    if (filter.rowsFilter.type === FILTER_TYPES.RANGE && filter.rowsFilter.range) {
      const { min, max } = filter.rowsFilter.range;
      rowsIndices = rowTimeIndices
        .map((value, index) => ({ value, index }))
        .filter(({ value }) => value >= min && value <= max)
        .map(({ index }) => index);
    } else if (filter.rowsFilter.type === FILTER_TYPES.MODULO && filter.rowsFilter.modulo) {
      const { divisor, remainder } = filter.rowsFilter.modulo;
      rowsIndices = rowTimeIndices
        .map((value, index) => ({ value, index }))
        .filter(({ value }) => value % divisor === remainder)
        .map(({ index }) => index);
    } else if (filter.rowsFilter.type === FILTER_TYPES.LIST && filter.rowsFilter.list) {
      rowsIndices = rowTimeIndices
        .map((value, index) => ({ value, index }))
        .filter(({ value }) => filter.rowsFilter.list?.includes(value))
        .map(({ index }) => index);
    }

    return { columnsIndices, rowsIndices };
  }, [currentState.data, filter, dateTime, isTimeSeries]);

  const applyOperation = () => {
    if (!filter.active || currentState.data.length === 0) {
      return;
    }

    const { columnsIndices, rowsIndices } = filteredData;
    const { type: opType, value } = filter.operation;

    // Create a deep copy of the matrix data
    const newData = currentState.data.map((row) => [...row]);

    // Apply the operation to each filtered cell - using for...of instead of forEach
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
      aggregates: {},
      // TODO recalculate aggregates
    });
  };

  const resetFilters = () => {
    setFilter({
      ...filter,
      active: false,
      columnsFilter: {
        type: FILTER_TYPES.RANGE,
        range: { min: 1, max: currentState.data[0]?.length || 1 },
      },
      rowsFilter: {
        indexingType: TIME_INDEXING.DAY_OF_MONTH,
        type: FILTER_TYPES.RANGE,
        range: { min: 1, max: currentState.data.length || 1 },
      },
    });
  };

  const toggleDrawer = () => {
    setOpen(!open);
  };

  const toggleFilter = () => {
    setFilter({ ...filter, active: !filter.active });
  };

  const renderFilterSummary = () => {
    if (!filter.active) {
      return null;
    }

    const { columnsFilter, rowsFilter } = filter;
    let columnFilterText = "";
    let rowFilterText = "";

    // Column filter summary
    if (columnsFilter.type === FILTER_TYPES.RANGE && columnsFilter.range) {
      columnFilterText = `${t("matrix.filter.columns")}: ${columnsFilter.range.min} - ${columnsFilter.range.max}`;
    } else if (columnsFilter.type === FILTER_TYPES.MODULO && columnsFilter.modulo) {
      columnFilterText = `${t("matrix.filter.columns")}: ${t("matrix.filter.modulo")} ${columnsFilter.modulo.divisor}/${columnsFilter.modulo.remainder}`;
    } else if (columnsFilter.type === FILTER_TYPES.LIST && columnsFilter.list) {
      columnFilterText = `${t("matrix.filter.columns")}: [${columnsFilter.list.join(", ")}]`;
    }

    // Row filter summary
    const indexType = t(`matrix.filter.indexing.${rowsFilter.indexingType}`);
    if (rowsFilter.type === FILTER_TYPES.RANGE && rowsFilter.range) {
      rowFilterText = `${t("matrix.filter.rows")} (${indexType}): ${rowsFilter.range.min} - ${rowsFilter.range.max}`;
    } else if (rowsFilter.type === FILTER_TYPES.MODULO && rowsFilter.modulo) {
      rowFilterText = `${t("matrix.filter.rows")} (${indexType}): ${t("matrix.filter.modulo")} ${rowsFilter.modulo.divisor}/${rowsFilter.modulo.remainder}`;
    } else if (rowsFilter.type === FILTER_TYPES.LIST && rowsFilter.list) {
      rowFilterText = `${t("matrix.filter.rows")} (${indexType}): [${rowsFilter.list.join(", ")}]`;
    }

    return (
      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        {columnFilterText && (
          <Chip label={columnFilterText} size="small" color="primary" variant="outlined" />
        )}
        {rowFilterText && (
          <Chip label={rowFilterText} size="small" color="primary" variant="outlined" />
        )}
      </Stack>
    );
  };

  const renderColumnFilter = () => (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.columnsFilter")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.columnsFilter.type}
            label={t("matrix.filter.type")}
            onChange={(e) =>
              setFilter({
                ...filter,
                columnsFilter: {
                  ...filter.columnsFilter,
                  type: e.target.value,
                },
              })
            }
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.MODULO}>{t("matrix.filter.modulo")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {filter.columnsFilter.type === FILTER_TYPES.RANGE && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.min")}
              type="number"
              value={filter.columnsFilter.range?.min || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  columnsFilter: {
                    ...filter.columnsFilter,
                    range: {
                      ...filter.columnsFilter.range,
                      min: Number.parseInt(e.target.value) || 1,
                    } as { min: number; max: number },
                  },
                })
              }
              fullWidth
            />
            <TextField
              label={t("matrix.filter.max")}
              type="number"
              value={filter.columnsFilter.range?.max || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  columnsFilter: {
                    ...filter.columnsFilter,
                    range: {
                      ...filter.columnsFilter.range,
                      max: Number.parseInt(e.target.value) || 1,
                    } as { min: number; max: number },
                  },
                })
              }
              fullWidth
            />
          </Box>
        )}

        {filter.columnsFilter.type === FILTER_TYPES.MODULO && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.divisor")}
              type="number"
              value={filter.columnsFilter.modulo?.divisor || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  columnsFilter: {
                    ...filter.columnsFilter,
                    modulo: {
                      ...filter.columnsFilter.modulo,
                      divisor: Number.parseInt(e.target.value) || 1,
                    } as { divisor: number; remainder: number },
                  },
                })
              }
              fullWidth
            />
            <TextField
              label={t("matrix.filter.remainder")}
              type="number"
              value={filter.columnsFilter.modulo?.remainder || 0}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  columnsFilter: {
                    ...filter.columnsFilter,
                    modulo: {
                      ...filter.columnsFilter.modulo,
                      remainder: Number.parseInt(e.target.value) || 0,
                    } as { divisor: number; remainder: number },
                  },
                })
              }
              fullWidth
            />
          </Box>
        )}

        {filter.columnsFilter.type === FILTER_TYPES.LIST && (
          <TextField
            label={t("matrix.filter.listValues")}
            placeholder="e.g., 1,3,5,7"
            fullWidth
            margin="dense"
            value={filter.columnsFilter.list?.join(",") || ""}
            onChange={(e) => {
              const values = e.target.value
                .split(",")
                .map((val) => Number.parseInt(val.trim()))
                .filter((val) => !Number.isNaN(val));

              setFilter({
                ...filter,
                columnsFilter: {
                  ...filter.columnsFilter,
                  list: values,
                },
              });
            }}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );

  const renderRowsFilter = () => (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.rowsFilter")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.indexingType")}</InputLabel>
          <Select
            value={filter.rowsFilter.indexingType}
            label={t("matrix.filter.indexingType")}
            onChange={(e) =>
              setFilter({
                ...filter,
                rowsFilter: {
                  ...filter.rowsFilter,
                  indexingType: e.target.value,
                },
              })
            }
          >
            <MenuItem value={TIME_INDEXING.DAY_OF_MONTH}>
              {t("matrix.filter.indexing.dayOfMonth")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.DAY_OF_YEAR}>
              {t("matrix.filter.indexing.dayOfYear")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.DAY_HOUR}>
              {t("matrix.filter.indexing.dayHour")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.HOUR_YEAR}>
              {t("matrix.filter.indexing.hourYear")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.MONTH}>{t("matrix.filter.indexing.month")}</MenuItem>
            <MenuItem value={TIME_INDEXING.WEEK}>{t("matrix.filter.indexing.week")}</MenuItem>
            <MenuItem value={TIME_INDEXING.WEEKDAY}>{t("matrix.filter.indexing.weekday")}</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.rowsFilter.type}
            label={t("matrix.filter.type")}
            onChange={(e) =>
              setFilter({
                ...filter,
                rowsFilter: {
                  ...filter.rowsFilter,
                  type: e.target.value,
                },
              })
            }
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.MODULO}>{t("matrix.filter.modulo")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {filter.rowsFilter.type === FILTER_TYPES.RANGE && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.min")}
              type="number"
              value={filter.rowsFilter.range?.min || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  rowsFilter: {
                    ...filter.rowsFilter,
                    range: {
                      ...filter.rowsFilter.range,
                      min: Number.parseInt(e.target.value) || 1,
                    } as { min: number; max: number },
                  },
                })
              }
              fullWidth
            />
            <TextField
              label={t("matrix.filter.max")}
              type="number"
              value={filter.rowsFilter.range?.max || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  rowsFilter: {
                    ...filter.rowsFilter,
                    range: {
                      ...filter.rowsFilter.range,
                      max: Number.parseInt(e.target.value) || 1,
                    } as { min: number; max: number },
                  },
                })
              }
              fullWidth
            />
          </Box>
        )}

        {filter.rowsFilter.type === FILTER_TYPES.MODULO && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.divisor")}
              type="number"
              value={filter.rowsFilter.modulo?.divisor || 1}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  rowsFilter: {
                    ...filter.rowsFilter,
                    modulo: {
                      ...filter.rowsFilter.modulo,
                      divisor: Number.parseInt(e.target.value) || 1,
                    } as { divisor: number; remainder: number },
                  },
                })
              }
              fullWidth
            />
            <TextField
              label={t("matrix.filter.remainder")}
              type="number"
              value={filter.rowsFilter.modulo?.remainder || 0}
              onChange={(e) =>
                setFilter({
                  ...filter,
                  rowsFilter: {
                    ...filter.rowsFilter,
                    modulo: {
                      ...filter.rowsFilter.modulo,
                      remainder: Number.parseInt(e.target.value) || 0,
                    } as { divisor: number; remainder: number },
                  },
                })
              }
              fullWidth
            />
          </Box>
        )}

        {filter.rowsFilter.type === FILTER_TYPES.LIST && (
          <TextField
            label={t("matrix.filter.listValues")}
            placeholder="e.g., 1,3,5,7"
            fullWidth
            margin="dense"
            value={filter.rowsFilter.list?.join(",") || ""}
            onChange={(e) => {
              const values = e.target.value
                .split(",")
                .map((val) => Number.parseInt(val.trim()))
                .filter((val) => !Number.isNaN(val));

              setFilter({
                ...filter,
                rowsFilter: {
                  ...filter.rowsFilter,
                  list: values,
                },
              });
            }}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );

  const renderOperation = () => (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.operation")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.operationType")}</InputLabel>
          <Select
            value={filter.operation.type}
            label={t("matrix.filter.operationType")}
            onChange={(e) =>
              setFilter({
                ...filter,
                operation: {
                  ...filter.operation,
                  type: e.target.value,
                },
              })
            }
          >
            <MenuItem value={Operation.Eq}>{t("matrix.operation.equal")}</MenuItem>
            <MenuItem value={Operation.Add}>{t("matrix.operation.add")}</MenuItem>
            <MenuItem value={Operation.Sub}>{t("matrix.operation.subtract")}</MenuItem>
            <MenuItem value={Operation.Mul}>{t("matrix.operation.multiply")}</MenuItem>
            <MenuItem value={Operation.Div}>{t("matrix.operation.divide")}</MenuItem>
            <MenuItem value={Operation.Abs}>{t("matrix.operation.absolute")}</MenuItem>
          </Select>
        </FormControl>

        {filter.operation.type !== Operation.Abs && (
          <TextField
            label={t("matrix.filter.value")}
            type="number"
            value={filter.operation.value}
            onChange={(e) =>
              setFilter({
                ...filter,
                operation: {
                  ...filter.operation,
                  value: Number.parseFloat(e.target.value) || 0,
                },
              })
            }
            fullWidth
            margin="dense"
          />
        )}

        <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
          <Button
            variant="contained"
            color="primary"
            onClick={applyOperation}
            startIcon={<PlayArrowIcon />}
            disabled={!filter.active}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <>
      <Tooltip title={t("matrix.filter.filterData")}>
        <IconButton onClick={toggleDrawer} color={filter.active ? "primary" : "default"}>
          <FilterListIcon />
        </IconButton>
      </Tooltip>

      {renderFilterSummary()}

      <Drawer
        anchor="right"
        open={open}
        onClose={toggleDrawer}
        PaperProps={{
          sx: { width: "400px", p: 2 },
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
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <FormControl sx={{ mb: 2 }} fullWidth>
          <Button
            variant={filter.active ? "contained" : "outlined"}
            color={filter.active ? "primary" : "inherit"}
            onClick={toggleFilter}
            startIcon={<FilterListIcon />}
          >
            {filter.active ? t("matrix.filter.active") : t("matrix.filter.inactive")}
          </Button>
        </FormControl>

        <Divider sx={{ mb: 2 }} />

        {renderColumnFilter()}
        {renderRowsFilter()}
        {renderOperation()}

        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {t("matrix.filter.selectionSummary")}
          </Typography>
          <Typography>
            {t("matrix.filter.selectedRows")}: {filteredData.rowsIndices.length}
          </Typography>
          <Typography>
            {t("matrix.filter.selectedColumns")}: {filteredData.columnsIndices.length}
          </Typography>
          <Typography>
            {t("matrix.filter.selectedCells")}:{" "}
            {filteredData.rowsIndices.length * filteredData.columnsIndices.length}
          </Typography>
        </Box>
      </Drawer>
    </>
  );
}

export default MatrixFilter;
