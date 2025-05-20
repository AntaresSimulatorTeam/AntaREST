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

import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  TextField,
  Slider,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Stack,
  Chip,
  type SelectChangeEvent,
  InputAdornment,
  IconButton,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";
import type { RowFilterProps, RowFilter as RowFilterType } from "./types";
import { FILTER_TYPES, TIME_INDEXING, TEMPORAL_OPTIONS } from "./constants";
import { useMemo, useState } from "react";
import { getFilteredTemporalOptions } from "./utils";
import {
  extractValueFromDate,
  getDefaultRangeForIndexType,
  getLocalizedTimeLabels,
} from "./dateUtils";

function RowFilterComponent({
  filter,
  setFilter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  onRemoveFilter,
  filterId,
}: RowFilterProps) {
  const { t } = useTranslation();

  // Filter temporal options based on the current time frequency
  const filteredOptions = useMemo(
    () => getFilteredTemporalOptions(timeFrequency, TEMPORAL_OPTIONS),
    [timeFrequency],
  );

  // Find the specific row filter we're editing
  const rowFilter = useMemo(() => {
    return filter.rowsFilters.find((rf) => rf.id === filterId) || filter.rowsFilters[0];
  }, [filter.rowsFilters, filterId]);

  // We're now using the shared date utility function

  const availableValues = useMemo(() => {
    if (!dateTime || !isTimeSeries) {
      return getDefaultRangeForIndexType(rowFilter.indexingType);
    }

    try {
      // Extract values using the date utility function
      const values = dateTime.map((dateStr, index) =>
        extractValueFromDate(dateStr, rowFilter.indexingType, index),
      );

      if (values.length > 0) {
        // Use actual min/max from the data
        const min = Math.min(...values);
        const max = Math.max(...values);
        const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
        return { min, max, uniqueValues };
      }

      // If no values, use defaults for the indexing type
      return getDefaultRangeForIndexType(rowFilter.indexingType);
    } catch {
      // Error processing dates
      return getDefaultRangeForIndexType(rowFilter.indexingType);
    }
  }, [dateTime, isTimeSeries, rowFilter.indexingType]);

  const handleIndexingTypeChange = (e: SelectChangeEvent) => {
    const newType = e.target.value;

    // Create updated row filter with new indexing type
    const updatedRowFilter: RowFilterType = {
      ...rowFilter,
      indexingType: newType,
      // Set appropriate default ranges based on the indexing type
      range: getDefaultRangeForIndexType(newType),
    };

    // Update the filter state with the modified row filter
    const updatedFilters = filter.rowsFilters.map((rf) =>
      rf.id === rowFilter.id ? updatedRowFilter : rf,
    );

    setFilter({
      ...filter,
      rowsFilters: updatedFilters,
    });
  };

  const handleTypeChange = (e: SelectChangeEvent) => {
    const updatedFilters = filter.rowsFilters.map((rf) =>
      rf.id === rowFilter.id ? { ...rf, type: e.target.value } : rf,
    );

    setFilter({
      ...filter,
      rowsFilters: updatedFilters,
    });
  };

  const handleRangeChange = (field: "min" | "max", value: string) => {
    const updatedFilters = filter.rowsFilters.map((rf) => {
      if (rf.id === rowFilter.id) {
        return {
          ...rf,
          range: {
            ...rf.range,
            [field]: Number.parseInt(value) || 1,
          } as { min: number; max: number },
        };
      }
      return rf;
    });

    setFilter({
      ...filter,
      rowsFilters: updatedFilters,
    });
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      const updatedFilters = filter.rowsFilters.map((rf) => {
        if (rf.id === rowFilter.id) {
          return {
            ...rf,
            range: {
              min: newValue[0],
              max: newValue[1],
            },
          };
        }
        return rf;
      });

      setFilter({
        ...filter,
        rowsFilters: updatedFilters,
      });
    }
  };

  const [inputValue, setInputValue] = useState<string>("");

  const handleListChange = (value: string) => {
    setInputValue(value);
  };

  const addValueToList = () => {
    const newValue = Number.parseInt(inputValue.trim());
    if (!Number.isNaN(newValue)) {
      // Only add if the value is not already in the list
      if (!rowFilter.list?.includes(newValue)) {
        const updatedFilters = filter.rowsFilters.map((rf) => {
          if (rf.id === rowFilter.id) {
            return {
              ...rf,
              list: [...(rf.list || []), newValue].sort((a, b) => a - b),
            };
          }
          return rf;
        });

        setFilter({
          ...filter,
          rowsFilters: updatedFilters,
        });
      }

      // Clear the input field after adding
      setInputValue("");
    }
  };

  const removeValueFromList = (valueToRemove: number) => {
    const updatedFilters = filter.rowsFilters.map((rf) => {
      if (rf.id === rowFilter.id) {
        return {
          ...rf,
          list: (rf.list || []).filter((value) => value !== valueToRemove),
        };
      }
      return rf;
    });

    setFilter({
      ...filter,
      rowsFilters: updatedFilters,
    });
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addValueToList();
    }
  };

  const handleCheckboxChange = (value: number) => {
    const currentList = rowFilter.list || [];
    const newList = currentList.includes(value)
      ? currentList.filter((item: number) => item !== value)
      : [...currentList, value];

    const updatedFilters = filter.rowsFilters.map((rf) => {
      if (rf.id === rowFilter.id) {
        return {
          ...rf,
          list: newList,
        };
      }
      return rf;
    });

    setFilter({
      ...filter,
      rowsFilters: updatedFilters,
    });
  };

  const renderFilterControls = () => {
    const { type, indexingType } = rowFilter;

    if (type === FILTER_TYPES.RANGE) {
      // For range type, we'll use different controls based on the indexing type
      if (
        [
          TIME_INDEXING.DAY_OF_MONTH,
          TIME_INDEXING.MONTH,
          TIME_INDEXING.WEEKDAY,
          TIME_INDEXING.DAY_HOUR,
          TIME_INDEXING.WEEK,
        ].includes(indexingType)
      ) {
        // Use a slider for these types
        const { min, max } = rowFilter.range || { min: 1, max: 100 };
        const marks = [];

        // Create appropriate marks based on indexing type
        if (indexingType === TIME_INDEXING.MONTH) {
          // Get month labels using our date utility
          const months = getLocalizedTimeLabels("month", t);
          marks.push(
            ...[1, 3, 6, 9, 12].map((value) => ({
              value,
              label: months[value - 1].shortLabel.charAt(0),
            })),
          );
        } else if (indexingType === TIME_INDEXING.WEEKDAY) {
          // Get weekday labels using our date utility
          const weekdays = getLocalizedTimeLabels("weekday", t);
          marks.push(
            ...[1, 2, 3, 4, 5, 6, 7].map((value) => ({
              value,
              label: weekdays[value - 1].shortLabel.charAt(0),
            })),
          );
        } else if (indexingType === TIME_INDEXING.DAY_HOUR) {
          marks.push(...[1, 6, 12, 18, 24].map((value) => ({ value, label: value.toString() })));
        } else {
          // For day of month or week
          const maxValue = indexingType === TIME_INDEXING.DAY_OF_MONTH ? 31 : 53;
          const step = indexingType === TIME_INDEXING.DAY_OF_MONTH ? 5 : 10;
          for (let i = 1; i <= maxValue; i += step) {
            marks.push({ value: i, label: i.toString() });
          }
          if (!marks.some((m) => m.value === maxValue)) {
            marks.push({ value: maxValue, label: maxValue.toString() });
          }
        }

        return (
          <Box sx={{ px: 2, pt: 3, pb: 1 }}>
            <Slider
              value={[min, max]}
              onChange={handleSliderChange}
              valueLabelDisplay="auto"
              min={availableValues.min}
              max={availableValues.max}
              marks={marks}
              sx={{ mt: 2 }}
            />

            <Box sx={{ display: "flex", justifyContent: "space-between", mt: 2 }}>
              <TextField
                label={t("matrix.filter.min")}
                type="number"
                size="small"
                value={min}
                onChange={(e) => handleRangeChange("min", e.target.value)}
                sx={{ width: "45%" }}
                InputProps={{
                  inputProps: {
                    min: availableValues.min,
                    max: availableValues.max,
                  },
                }}
              />
              <TextField
                label={t("matrix.filter.max")}
                type="number"
                size="small"
                value={max}
                onChange={(e) => handleRangeChange("max", e.target.value)}
                sx={{ width: "45%" }}
                InputProps={{
                  inputProps: {
                    min: availableValues.min,
                    max: availableValues.max,
                  },
                }}
              />
            </Box>
          </Box>
        );
      }

      // For other types (DAY_OF_YEAR, HOUR_YEAR), use text fields
      return (
        <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
          <TextField
            label={t("matrix.filter.min")}
            type="number"
            value={rowFilter.range?.min || 1}
            onChange={(e) => handleRangeChange("min", e.target.value)}
            fullWidth
          />
          <TextField
            label={t("matrix.filter.max")}
            type="number"
            value={rowFilter.range?.max || 1}
            onChange={(e) => handleRangeChange("max", e.target.value)}
            fullWidth
          />
        </Box>
      );
    }
    if (type === FILTER_TYPES.LIST) {
      // For list type, we'll use different controls based on the indexing type
      if (indexingType === TIME_INDEXING.WEEKDAY) {
        // Get localized weekday labels
        const weekdays = getLocalizedTimeLabels("weekday", t);

        return (
          <FormGroup sx={{ mt: 2 }}>
            {weekdays.map((day) => (
              <FormControlLabel
                key={day.value}
                control={
                  <Checkbox
                    checked={(rowFilter.list || []).includes(day.value)}
                    onChange={() => handleCheckboxChange(day.value)}
                  />
                }
                label={day.label}
              />
            ))}
          </FormGroup>
        );
      }

      if (indexingType === TIME_INDEXING.MONTH) {
        // Get localized month labels
        const months = getLocalizedTimeLabels("month", t);

        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t("matrix.filter.selectMonths")}
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {months.map((month) => {
                const isSelected = (rowFilter.list || []).includes(month.value);
                return (
                  <Chip
                    key={month.value}
                    label={month.label}
                    onClick={() => handleCheckboxChange(month.value)}
                    color={isSelected ? "primary" : "default"}
                    variant={isSelected ? "filled" : "outlined"}
                    sx={{ my: 0.5 }}
                  />
                );
              })}
            </Stack>
          </Box>
        );
      }

      if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
        // Grid of days for day of month
        const days = Array.from({ length: 31 }, (_, i) => i + 1);

        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t("matrix.filter.selectDays")}
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              {days.map((day) => {
                const isSelected = (rowFilter.list || []).includes(day);
                return (
                  <Chip
                    key={day}
                    label={day}
                    onClick={() => handleCheckboxChange(day)}
                    color={isSelected ? "primary" : "default"}
                    variant={isSelected ? "filled" : "outlined"}
                    size="small"
                    sx={{ m: 0.2, width: 40 }}
                  />
                );
              })}
            </Stack>
          </Box>
        );
      }

      // For other indexing types, use a text field with chips display
      return (
        <>
          <TextField
            label={t("matrix.filter.listValues")}
            placeholder={t("matrix.filter.enterValue")}
            fullWidth
            margin="dense"
            value={inputValue}
            onChange={(e) => handleListChange(e.target.value)}
            onKeyDown={handleKeyPress}
            type="number"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={addValueToList}
                    disabled={!inputValue.trim()}
                    edge="end"
                    size="small"
                  >
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            helperText={t("matrix.filter.pressEnterOrComma")}
          />
          {(rowFilter.list?.length || 0) > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" display="block" gutterBottom>
                {t("matrix.filter.selectedValues")}:
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {rowFilter.list?.map((value) => (
                  <Chip
                    key={value}
                    label={value}
                    size="small"
                    color="primary"
                    onDelete={() => removeValueFromList(value)}
                    sx={{ m: 0.5 }}
                  />
                ))}
              </Stack>
            </Box>
          )}
        </>
      );
    }

    return null;
  };

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
          }}
        >
          <Typography variant="subtitle1">{t("matrix.filter.rowsFilter")}</Typography>
          {onRemoveFilter && filter.rowsFilters.length > 1 && (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFilter(rowFilter.id);
              }}
              sx={{ ml: 1 }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.indexingType")}</InputLabel>
          <Select
            value={rowFilter.indexingType}
            label={t("matrix.filter.indexingType")}
            onChange={handleIndexingTypeChange}
          >
            {filteredOptions.map((option: { value: string; label: string }) => (
              <MenuItem key={option.value} value={option.value}>
                {t(`matrix.filter.indexing.${option.value}`)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={rowFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChange}
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {renderFilterControls()}
      </AccordionDetails>
    </Accordion>
  );
}

export default RowFilterComponent;
