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

  // Memoize the default range values for each indexing type to prevent recalculations
  const indexTypeRanges = useMemo(() => {
    // Create a map of all default ranges
    const ranges = Object.values(TIME_INDEXING).reduce(
      (acc, type) => {
        acc[type] = getDefaultRangeForIndexType(type);
        return acc;
      },
      {} as Record<string, { min: number; max: number }>,
    );

    return ranges;
  }, []);

  // Get the range values based on data or defaults - only dependent on data and time frequency
  // NOT dependent on rowFilter to avoid infinite loops
  const valuesByIndexType = useMemo(() => {
    // Start with default ranges for all indexing types
    const result = { ...indexTypeRanges } as Record<
      string,
      { min: number; max: number; uniqueValues?: number[] }
    >;

    // Add unique values arrays to fixed range types
    result[TIME_INDEXING.DAY_HOUR] = {
      min: 1,
      max: 24,
      uniqueValues: Array.from({ length: 24 }, (_, i) => i + 1),
    };

    result[TIME_INDEXING.WEEKDAY] = {
      min: 1,
      max: 7,
      uniqueValues: Array.from({ length: 7 }, (_, i) => i + 1),
    };

    result[TIME_INDEXING.MONTH] = {
      min: 1,
      max: 12,
      uniqueValues: Array.from({ length: 12 }, (_, i) => i + 1),
    };

    // Only try to extract data-based values if we have time series data
    if (dateTime && isTimeSeries && dateTime.length > 0) {
      // Only update the ranges that should be data-dependent
      const dynamicTypes = [
        TIME_INDEXING.DAY_OF_YEAR,
        TIME_INDEXING.HOUR_YEAR,
        TIME_INDEXING.DAY_OF_MONTH,
        TIME_INDEXING.WEEK,
      ];

      for (const indexType of dynamicTypes) {
        try {
          const values = dateTime.map((dateStr, index) =>
            extractValueFromDate(dateStr, indexType, index),
          );

          if (values.length > 0) {
            const min = Math.min(...values);
            const max = Math.max(...values);
            const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
            result[indexType] = { min, max, uniqueValues };
          }
        } catch {
          // Keep defaults on error
        }
      }
    }

    return result;
  }, [dateTime, isTimeSeries, indexTypeRanges]);

  // Get current values for the selected indexing type
  const availableValues = useMemo(
    () => valuesByIndexType[rowFilter.indexingType],
    [valuesByIndexType, rowFilter.indexingType],
  );

  const handleIndexingTypeChange = (e: SelectChangeEvent) => {
    const newType = e.target.value;

    // Get the appropriate available values for this indexing type
    const availableValuesForType = valuesByIndexType[newType];

    // Create updated row filter with new indexing type
    const updatedRowFilter: RowFilterType = {
      ...rowFilter,
      indexingType: newType,
      // Use the calculated values or defaults
      range: {
        min: availableValuesForType.min,
        max: availableValuesForType.max,
      },
      // Reset list when changing index type to avoid invalid values
      list: [],
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

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      // Simply use the values from the slider - they're already constrained by the min/max props
      const [min, max] = newValue;

      const updatedFilters = filter.rowsFilters.map((rf) => {
        if (rf.id === rowFilter.id) {
          return {
            ...rf,
            range: { min, max },
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

  // Memoize all slider marks by indexing type, not dependent on rowFilter
  const allMarks = useMemo(() => {
    const marksMap: Record<string, Array<{ value: number; label: string }>> = {};

    // MONTH
    const months = getLocalizedTimeLabels("month", t);
    marksMap[TIME_INDEXING.MONTH] = [1, 3, 6, 9, 12].map((value) => ({
      value,
      label: months[value - 1].shortLabel.charAt(0),
    }));

    // WEEKDAY
    const weekdays = getLocalizedTimeLabels("weekday", t);
    marksMap[TIME_INDEXING.WEEKDAY] = [1, 2, 3, 4, 5, 6, 7].map((value) => ({
      value,
      label: weekdays[value - 1].shortLabel.charAt(0),
    }));

    // DAY_HOUR
    marksMap[TIME_INDEXING.DAY_HOUR] = [1, 4, 8, 12, 16, 20, 24].map((value) => ({
      value,
      label: value.toString(),
    }));

    // DAY_OF_YEAR
    marksMap[TIME_INDEXING.DAY_OF_YEAR] = [1, 91, 182, 273, 366].map((value) => ({
      value,
      label: value.toString(),
    }));

    // HOUR_YEAR - use markers with more readable labels
    marksMap[TIME_INDEXING.HOUR_YEAR] = [
      { value: 1, label: "Jan" },
      { value: 1440, label: "Feb" },
      { value: 2880, label: "Mar" },
      { value: 4320, label: "May" },
      { value: 5760, label: "Jul" },
      { value: 7200, label: "Sep" },
      { value: 8760, label: "Dec" },
    ];

    // DAY_OF_MONTH
    marksMap[TIME_INDEXING.DAY_OF_MONTH] = [];
    for (let i = 1; i <= 31; i += 5) {
      marksMap[TIME_INDEXING.DAY_OF_MONTH].push({ value: i, label: i.toString() });
    }
    if (!marksMap[TIME_INDEXING.DAY_OF_MONTH].some((m) => m.value === 31)) {
      marksMap[TIME_INDEXING.DAY_OF_MONTH].push({ value: 31, label: "31" });
    }

    // WEEK
    marksMap[TIME_INDEXING.WEEK] = [];
    for (let i = 1; i <= 53; i += 10) {
      marksMap[TIME_INDEXING.WEEK].push({ value: i, label: i.toString() });
    }
    if (!marksMap[TIME_INDEXING.WEEK].some((m) => m.value === 53)) {
      marksMap[TIME_INDEXING.WEEK].push({ value: 53, label: "53" });
    }

    return marksMap;
  }, [t]);

  // Get marks for current indexing type
  const sliderMarks = useMemo(
    () => allMarks[rowFilter.indexingType] || [],
    [allMarks, rowFilter.indexingType],
  );

  const renderRangeControls = () => {
    const { indexingType } = rowFilter;
    const { min, max } = rowFilter.range || availableValues;

    // Use simple clamped values within the available range
    const sliderMin = availableValues.min;
    const sliderMax = availableValues.max;
    const validMin = Math.min(Math.max(min, sliderMin), sliderMax);
    const validMax = Math.min(Math.max(max, sliderMin), sliderMax);

    if (indexingType === TIME_INDEXING.HOUR_YEAR) {
      // Convert hours to human-readable format
      const formatHourOfYear = (hour: number): string => {
        const months = [
          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec",
        ];

        const daysPerMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

        // Ensure we have a positive hour value
        const safeHour = Math.max(1, hour);
        let remainingHours = safeHour - 1; // 0-based for calculation

        // Calculate month
        let monthIndex = 0;
        while (monthIndex < 12 && remainingHours >= daysPerMonth[monthIndex] * 24) {
          remainingHours -= daysPerMonth[monthIndex] * 24;
          monthIndex++;
        }

        // Calculate day and hour
        const dayOfMonth = Math.floor(remainingHours / 24) + 1;
        const hourOfDay = remainingHours % 24;

        // Format: "Jan 1, 5h" (5th hour of Jan 1st)
        return `${months[monthIndex]} ${dayOfMonth}, ${hourOfDay}h`;
      };

      return (
        <Box sx={{ px: 2, pt: 3, pb: 1 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Hour of year range:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: "medium" }}>
              {formatHourOfYear(validMin)} - {formatHourOfYear(validMax)}
            </Typography>
          </Box>

          <Slider
            value={[validMin, validMax]}
            onChange={handleSliderChange}
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => formatHourOfYear(value)}
            min={sliderMin}
            max={sliderMax}
            marks={sliderMarks}
            step={1}
            sx={{ mt: 1 }}
          />

          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
            Tip: For more precise filtering, consider using multiple filters or the list mode
          </Typography>
        </Box>
      );
    }

    // Standard range handling for other types
    return (
      <Box sx={{ px: 2, pt: 3, pb: 1 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "flex", justifyContent: "space-between" }}
        >
          <span>{validMin}</span>
          <span>{validMax}</span>
        </Typography>
        <Slider
          value={[validMin, validMax]}
          onChange={handleSliderChange}
          valueLabelDisplay="auto"
          min={sliderMin}
          max={sliderMax}
          marks={sliderMarks}
          step={1}
          sx={{ mt: 1 }}
        />
      </Box>
    );
  };

  const renderListControls = () => {
    const { indexingType } = rowFilter;

    if (indexingType === TIME_INDEXING.HOUR_YEAR) {
      // Common time periods as quick selections
      const commonPeriods = [
        { value: 1, label: "Jan 1" },
        { value: 24, label: "Jan 2" },
        { value: 48, label: "Jan 3" },
        { value: 168, label: "Jan 8 (week 1)" },
        { value: 336, label: "Jan 15 (week 2)" },
        { value: 744, label: "Feb 1" },
        { value: 1416, label: "Mar 1" },
        { value: 2160, label: "Apr 1" },
        { value: 2880, label: "May 1" },
        { value: 3624, label: "Jun 1" },
        { value: 4344, label: "Jul 1" },
        { value: 5088, label: "Aug 1" },
        { value: 5832, label: "Sep 1" },
        { value: 6552, label: "Oct 1" },
        { value: 7296, label: "Nov 1" },
        { value: 8016, label: "Dec 1" },
      ];

      return (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Common time periods:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {commonPeriods.map((period) => {
              const isSelected = (rowFilter.list || []).includes(period.value);

              return (
                <Chip
                  key={period.value}
                  label={period.label}
                  onClick={() => handleCheckboxChange(period.value)}
                  color={isSelected ? "primary" : "default"}
                  variant={isSelected ? "filled" : "outlined"}
                  sx={{ my: 0.5 }}
                />
              );
            })}
          </Stack>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mt: 2, mb: 1 }}
          >
            Or add specific hours manually:
          </Typography>

          <TextField
            label={t("matrix.filter.listValues")}
            placeholder="Enter hour number (1-8760)"
            fullWidth
            margin="dense"
            value={inputValue}
            onChange={(e) => handleListChange(e.target.value)}
            onKeyDown={handleKeyPress}
            type="number"
            slotProps={{
              input: {
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
              },
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
        </Box>
      );
    }

    if (indexingType === TIME_INDEXING.WEEKDAY) {
      // Get localized weekday labels
      const weekdays = getLocalizedTimeLabels("weekday", t);

      return (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t("matrix.filter.selectDays")}
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {weekdays.map((day) => {
              const isSelected = (rowFilter.list || []).includes(day.value);

              return (
                <Chip
                  key={day.value}
                  label={day.label}
                  onClick={() => handleCheckboxChange(day.value)}
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
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ maxWidth: "100%" }}>
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
                  sx={{ m: 0.2, minWidth: 36, height: 24 }}
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
          slotProps={{
            input: {
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
            },
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
  };

  const renderFilterControls = () => {
    const { type } = rowFilter;

    if (type === FILTER_TYPES.RANGE) {
      return renderRangeControls();
    }

    if (type === FILTER_TYPES.LIST) {
      return renderListControls();
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
