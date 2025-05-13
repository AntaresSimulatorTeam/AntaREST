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
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import type { RowFilterProps } from "./types";
import { FILTER_TYPES, TIME_INDEXING, TEMPORAL_OPTIONS } from "./constants";
import { useMemo } from "react";
import { getFilteredTemporalOptions } from "./utils";

function RowFilter({ filter, setFilter, dateTime, isTimeSeries, timeFrequency }: RowFilterProps) {
  const { t } = useTranslation();

  // Filter temporal options based on the current time frequency
  const filteredOptions = useMemo(
    () => getFilteredTemporalOptions(timeFrequency, TEMPORAL_OPTIONS),
    [timeFrequency],
  );

  const availableValues = useMemo(() => {
    if (!dateTime || !isTimeSeries) {
      return { min: 1, max: 100 };
    }

    try {
      // Extract values using the same pattern matching approach as in utils.ts
      const values = dateTime.map((dateStr, index) => {
        const { indexingType } = filter.rowsFilter;

        if (indexingType === TIME_INDEXING.MONTH) {
          const months = [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
            "jan",
            "fév",
            "mar",
            "avr",
            "mai",
            "juin",
            "juil",
            "aoû",
            "sep",
            "oct",
            "nov",
            "déc",
          ];

          for (let i = 0; i < months.length; i++) {
            if (dateStr.toLowerCase().includes(months[i])) {
              return (i % 12) + 1;
            }
          }
        } else if (indexingType === TIME_INDEXING.WEEKDAY) {
          const days = [
            "mon",
            "tue",
            "wed",
            "thu",
            "fri",
            "sat",
            "sun",
            "lun",
            "mar",
            "mer",
            "jeu",
            "ven",
            "sam",
            "dim",
          ];

          for (let i = 0; i < days.length; i++) {
            if (dateStr.toLowerCase().includes(days[i])) {
              return (i % 7) + 1;
            }
          }
        } else if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
          const match = dateStr.match(/\b([1-9]|[12]\d|3[01])\b/);
          if (match) {
            return Number.parseInt(match[0]);
          }
        } else if (indexingType === TIME_INDEXING.DAY_HOUR) {
          const match = dateStr.match(/(\d{1,2})[:h]/);
          if (match) {
            return Number.parseInt(match[1]) + 1;
          }
        }

        // Default to index if we can't extract a value
        return index + 1;
      });

      // Set reasonable defaults based on the indexing type
      let min = 1;
      let max = 100;

      if (values.length > 0) {
        min = Math.min(...values);
        max = Math.max(...values);
      } else {
        // Set appropriate defaults based on the indexing type
        switch (filter.rowsFilter.indexingType) {
          case TIME_INDEXING.DAY_OF_MONTH:
            max = 31;
            break;
          case TIME_INDEXING.MONTH:
            max = 12;
            break;
          case TIME_INDEXING.WEEKDAY:
            max = 7;
            break;
          case TIME_INDEXING.DAY_HOUR:
            max = 24;
            break;
          case TIME_INDEXING.DAY_OF_YEAR:
            max = 366;
            break;
          case TIME_INDEXING.WEEK:
            max = 53;
            break;
          case TIME_INDEXING.HOUR_YEAR:
            max = 8760;
            break;
        }
      }

      const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
      return { min, max, uniqueValues };
    } catch (error) {
      console.error("Error processing dates:", error);
      return { min: 1, max: 100 };
    }
  }, [dateTime, isTimeSeries, filter.rowsFilter]);

  const handleIndexingTypeChange = (e: SelectChangeEvent) => {
    const newType = e.target.value;

    // Reset the filter values when changing indexing type
    const newFilter = {
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        indexingType: newType,
      },
    };

    // Set appropriate default ranges based on the indexing type
    switch (newType) {
      case TIME_INDEXING.DAY_OF_MONTH:
        newFilter.rowsFilter.range = { min: 1, max: 31 };
        break;
      case TIME_INDEXING.MONTH:
        newFilter.rowsFilter.range = { min: 1, max: 12 };
        break;
      case TIME_INDEXING.WEEKDAY:
        newFilter.rowsFilter.range = { min: 1, max: 7 };
        break;
      case TIME_INDEXING.DAY_HOUR:
        newFilter.rowsFilter.range = { min: 1, max: 24 };
        break;
      case TIME_INDEXING.DAY_OF_YEAR:
        newFilter.rowsFilter.range = { min: 1, max: 366 };
        break;
      case TIME_INDEXING.WEEK:
        newFilter.rowsFilter.range = { min: 1, max: 53 };
        break;
      case TIME_INDEXING.HOUR_YEAR:
        newFilter.rowsFilter.range = { min: 1, max: 8760 };
        break;
    }

    setFilter(newFilter);
  };

  const handleTypeChange = (e: SelectChangeEvent) => {
    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        type: e.target.value,
      },
    });
  };

  const handleRangeChange = (field: "min" | "max", value: string) => {
    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        range: {
          ...filter.rowsFilter.range,
          [field]: Number.parseInt(value) || 1,
        } as { min: number; max: number },
      },
    });
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      setFilter({
        ...filter,
        rowsFilter: {
          ...filter.rowsFilter,
          range: {
            min: newValue[0],
            max: newValue[1],
          },
        },
      });
    }
  };

  const handleModuloChange = (field: "divisor" | "remainder", value: string) => {
    const parsedValue =
      field === "divisor" ? Number.parseInt(value) || 1 : Number.parseInt(value) || 0;

    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        modulo: {
          ...filter.rowsFilter.modulo,
          [field]: parsedValue,
        } as { divisor: number; remainder: number },
      },
    });
  };

  const handleListChange = (value: string) => {
    const values = value
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
  };

  const handleCheckboxChange = (value: number) => {
    const currentList = filter.rowsFilter.list || [];
    const newList = currentList.includes(value)
      ? currentList.filter((item) => item !== value)
      : [...currentList, value];

    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        list: newList,
      },
    });
  };

  const renderFilterControls = () => {
    const { type, indexingType } = filter.rowsFilter;

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
        const { min, max } = filter.rowsFilter.range || { min: 1, max: 100 };
        const marks = [];

        // Create appropriate marks based on indexing type
        if (indexingType === TIME_INDEXING.MONTH) {
          marks.push(...[1, 3, 6, 9, 12].map((value) => ({ value, label: value.toString() })));
        } else if (indexingType === TIME_INDEXING.WEEKDAY) {
          marks.push(
            ...[1, 2, 3, 4, 5, 6, 7].map((value) => ({
              value,
              label: ["M", "T", "W", "T", "F", "S", "S"][value - 1],
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
            value={filter.rowsFilter.range?.min || 1}
            onChange={(e) => handleRangeChange("min", e.target.value)}
            fullWidth
          />
          <TextField
            label={t("matrix.filter.max")}
            type="number"
            value={filter.rowsFilter.range?.max || 1}
            onChange={(e) => handleRangeChange("max", e.target.value)}
            fullWidth
          />
        </Box>
      );
    }

    if (type === FILTER_TYPES.MODULO) {
      return (
        <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
          <TextField
            label={t("matrix.filter.divisor")}
            type="number"
            value={filter.rowsFilter.modulo?.divisor || 1}
            onChange={(e) => handleModuloChange("divisor", e.target.value)}
            fullWidth
          />
          <TextField
            label={t("matrix.filter.remainder")}
            type="number"
            value={filter.rowsFilter.modulo?.remainder || 0}
            onChange={(e) => handleModuloChange("remainder", e.target.value)}
            fullWidth
          />
        </Box>
      );
    }

    if (type === FILTER_TYPES.LIST) {
      // For list type, we'll use different controls based on the indexing type
      if (indexingType === TIME_INDEXING.WEEKDAY) {
        // Checkbox group for weekdays
        const weekdays = [
          { value: 1, label: t("date.monday") },
          { value: 2, label: t("date.tuesday") },
          { value: 3, label: t("date.wednesday") },
          { value: 4, label: t("date.thursday") },
          { value: 5, label: t("date.friday") },
          { value: 6, label: t("date.saturday") },
          { value: 7, label: t("date.sunday") },
        ];

        return (
          <FormGroup sx={{ mt: 2 }}>
            {weekdays.map((day) => (
              <FormControlLabel
                key={day.value}
                control={
                  <Checkbox
                    checked={(filter.rowsFilter.list || []).includes(day.value)}
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
        // Checkbox group for months
        const months = [
          { value: 1, label: t("date.january") },
          { value: 2, label: t("date.february") },
          { value: 3, label: t("date.march") },
          { value: 4, label: t("date.april") },
          { value: 5, label: t("date.may") },
          { value: 6, label: t("date.june") },
          { value: 7, label: t("date.july") },
          { value: 8, label: t("date.august") },
          { value: 9, label: t("date.september") },
          { value: 10, label: t("date.october") },
          { value: 11, label: t("date.november") },
          { value: 12, label: t("date.december") },
        ];

        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t("matrix.filter.selectMonths")}
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {months.map((month) => {
                const isSelected = (filter.rowsFilter.list || []).includes(month.value);
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
                const isSelected = (filter.rowsFilter.list || []).includes(day);
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

      // For other indexing types, use a text field
      return (
        <TextField
          label={t("matrix.filter.listValues")}
          placeholder="e.g., 1,3,5,7"
          fullWidth
          margin="dense"
          value={filter.rowsFilter.list?.join(",") || ""}
          onChange={(e) => handleListChange(e.target.value)}
        />
      );
    }

    return null;
  };

  return (
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
            value={filter.rowsFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChange}
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.MODULO}>{t("matrix.filter.modulo")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {renderFilterControls()}
      </AccordionDetails>
    </Accordion>
  );
}

export default RowFilter;
