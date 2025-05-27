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
  type SelectChangeEvent,
  IconButton,
  Tooltip,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";
import { useMemo, memo, useCallback } from "react";
import type { RowFilterProps, RowFilter } from "./types";
import {
  FILTER_TYPES,
  TEMPORAL_OPTIONS,
  TIME_INDEXING,
  type TimeIndexingType,
  type FilterType,
} from "./constants";
import {
  ACCORDION_STYLES,
  TYPOGRAPHY_STYLES,
  FORM_STYLES,
  DESIGN_TOKENS,
  CONTAINER_STYLES,
  ICON_BUTTON_STYLES,
} from "./styles";
import { useFilterControls } from "./hooks/useFilterControls";
import { useTemporalData } from "./hooks/useTemporalData";
import { getLocalizedTimeLabels } from "./dateUtils";
import { getFilteredTemporalOptions } from "./utils";
import TemporalFilterRenderer from "./components/TemporalFilterRenderer";

const RowFilterComponent = memo(
  ({
    filter,
    setFilter,
    dateTime,
    isTimeSeries,
    timeFrequency,
    onRemoveFilter,
    filterId,
    expanded = true,
    onToggleExpanded,
  }: RowFilterProps) => {
    const { t } = useTranslation();

    const {
      inputValue,
      handleListChange,
      addValueToList,
      removeValueFromList,
      clearAllValues,
      handleKeyPress,
      handleCheckboxChange,
      handleTypeChange: handleFilterTypeChange,
    } = useFilterControls({
      filter,
      setFilter,
      filterId,
    });

    const { valuesByIndexType } = useTemporalData({
      dateTime,
      isTimeSeries,
      timeFrequency,
    });

    // Filter temporal options based on the current time frequency
    const filteredOptions = useMemo(
      () => getFilteredTemporalOptions(timeFrequency, [...TEMPORAL_OPTIONS]),
      [timeFrequency],
    );

    const rowFilter = useMemo(() => {
      const foundFilter =
        filter.rowsFilters.find((rf) => rf.id === filterId) || filter.rowsFilters[0];

      return {
        id: foundFilter.id,
        indexingType: foundFilter.indexingType,
        type: foundFilter.type,
        range: foundFilter.range ? { ...foundFilter.range } : undefined,
        list: foundFilter.list ? [...foundFilter.list] : [],
      };
    }, [filter.rowsFilters, filterId]);

    // Get current values for the selected indexing type
    const availableValues = useMemo(
      () => valuesByIndexType[rowFilter.indexingType] || { min: 1, max: 100 },
      [valuesByIndexType, rowFilter.indexingType],
    );

    const rangeValue = useMemo(
      () =>
        [
          rowFilter.range?.min ?? availableValues.min,
          rowFilter.range?.max ?? availableValues.max,
        ] as [number, number],
      [rowFilter.range?.min, rowFilter.range?.max, availableValues.min, availableValues.max],
    );

    const handleAddValue = useCallback(() => {
      addValueToList(filterId);
    }, [addValueToList, filterId]);

    const handleRemoveValue = useCallback(
      (value: number) => {
        removeValueFromList(value, filterId);
      },
      [removeValueFromList, filterId],
    );

    const handleClearAll = useCallback(() => {
      clearAllValues(filterId);
    }, [clearAllValues, filterId]);

    const handleCheckbox = useCallback(
      (value: number) => {
        handleCheckboxChange(value, filterId);
      },
      [handleCheckboxChange, filterId],
    );

    const handleDeleteClick = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        onRemoveFilter?.(rowFilter.id);
      },
      [onRemoveFilter, rowFilter.id],
    );

    const handleIndexingTypeChange = useCallback(
      (e: SelectChangeEvent) => {
        const newType = e.target.value as TimeIndexingType;
        const availableValuesForType = valuesByIndexType[newType] || { min: 1, max: 100 };

        const updatedRowFilter: RowFilter = {
          ...rowFilter,
          indexingType: newType,
          range: {
            min: availableValuesForType.min,
            max: availableValuesForType.max,
          },
          list: [],
        };

        const updatedFilters = filter.rowsFilters.map((rf) =>
          rf.id === rowFilter.id ? updatedRowFilter : rf,
        );

        setFilter({
          ...filter,
          rowsFilters: updatedFilters,
        });
      },
      [filter, rowFilter, valuesByIndexType, setFilter],
    );

    const handleTypeChange = useCallback(
      (e: SelectChangeEvent) => {
        handleFilterTypeChange(e.target.value as FilterType, filterId);
      },
      [handleFilterTypeChange, filterId],
    );

    const handleRangeChange = useCallback(
      (newValues: [number, number]) => {
        // Prevent unnecessary updates if values haven't changed
        if (rowFilter.range?.min === newValues[0] && rowFilter.range?.max === newValues[1]) {
          return;
        }

        setFilter({
          ...filter,
          rowsFilters: filter.rowsFilters.map((rf) => {
            if (rf.id !== filterId) {
              return rf;
            }

            return {
              ...rf,
              range: { min: newValues[0], max: newValues[1] },
            };
          }),
        });
      },
      [filter, filterId, setFilter, rowFilter.range],
    );

    const sliderMarks = useMemo(() => {
      const { indexingType } = rowFilter;

      if (indexingType === TIME_INDEXING.MONTH) {
        const months = getLocalizedTimeLabels("month", t);
        return [1, 3, 6, 9, 12].map((value) => ({
          value,
          label: months[value - 1].shortLabel.charAt(0),
        }));
      }

      if (indexingType === TIME_INDEXING.WEEKDAY) {
        const weekdays = getLocalizedTimeLabels("weekday", t);
        return [1, 2, 3, 4, 5, 6, 7].map((value) => ({
          value,
          label: weekdays[value - 1].shortLabel.charAt(0),
        }));
      }

      if (indexingType === TIME_INDEXING.DAY_HOUR) {
        return [1, 4, 8, 12, 16, 20, 24].map((value) => ({
          value,
          label: value.toString(),
        }));
      }

      if (indexingType === TIME_INDEXING.DAY_OF_YEAR) {
        return [1, 91, 182, 273, 366].map((value) => ({
          value,
          label: value.toString(),
        }));
      }

      if (indexingType === TIME_INDEXING.HOUR_YEAR) {
        return [
          { value: 1, label: "Jan" },
          { value: 1440, label: "Feb" },
          { value: 2880, label: "Mar" },
          { value: 4320, label: "May" },
          { value: 5760, label: "Jul" },
          { value: 7200, label: "Sep" },
          { value: 8760, label: "Dec" },
        ];
      }

      if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
        const marks = [];
        const daysToMark = [1, 6, 11, 16, 21, 26, 31];

        for (const day of daysToMark) {
          if (day <= 31) {
            marks.push({ value: day, label: day.toString() });
          }
        }

        if (!marks.some((m) => m.value === 31)) {
          marks.push({ value: 31, label: "31" });
        }

        return marks;
      }

      if (indexingType === TIME_INDEXING.WEEK) {
        const marks = [];
        const weekValues = [1, 11, 21, 31, 41, 51, 53];

        for (const week of weekValues) {
          if (week <= 53) {
            marks.push({ value: week, label: week.toString() });
          }
        }

        if (!marks.some((m) => m.value === 53)) {
          marks.push({ value: 53, label: "53" });
        }

        return marks;
      }

      return [];
    }, [rowFilter, t]);

    return (
      <Accordion
        expanded={expanded}
        onChange={() => onToggleExpanded?.(rowFilter.id)}
        slotProps={{ transition: { unmountOnExit: true } }}
        sx={{ mb: DESIGN_TOKENS.spacing.sm }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon fontSize="small" />}
          sx={ACCORDION_STYLES.summary}
        >
          <Box sx={CONTAINER_STYLES.flexRow}>
            <Typography sx={TYPOGRAPHY_STYLES.sectionTitle}>
              {t("matrix.filter.rowsFilter")}
            </Typography>
          </Box>
          {onRemoveFilter && filter.rowsFilters.length > 1 && (
            <IconButton size="small" onClick={handleDeleteClick} sx={ICON_BUTTON_STYLES.small}>
              <DeleteIcon fontSize="small" sx={{ width: 13, height: 13 }} />
            </IconButton>
          )}
        </AccordionSummary>
        <AccordionDetails sx={ACCORDION_STYLES.details}>
          <Box sx={FORM_STYLES.sideBySideContainer}>
            <Tooltip title={t("matrix.filter.indexingType")} placement="top">
              <FormControl size="small" sx={{ flex: 1, ...FORM_STYLES.sideBySideFormControl }}>
                <InputLabel>{t("matrix.filter.indexingType")}</InputLabel>
                <Select
                  value={rowFilter.indexingType}
                  label={t("matrix.filter.indexingType")}
                  onChange={handleIndexingTypeChange}
                  sx={FORM_STYLES.sideBySideFormControl}
                >
                  {filteredOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value} sx={FORM_STYLES.menuItem}>
                      {t(`matrix.filter.indexing.${option.value}`)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Tooltip>

            <Tooltip title={t("matrix.filter.type")} placement="top">
              <FormControl size="small" sx={{ flex: 1, ...FORM_STYLES.sideBySideFormControl }}>
                <InputLabel>{t("matrix.filter.type")}</InputLabel>
                <Select
                  value={rowFilter.type}
                  label={t("matrix.filter.type")}
                  onChange={handleTypeChange}
                  sx={FORM_STYLES.sideBySideFormControl}
                >
                  <MenuItem value={FILTER_TYPES.RANGE} sx={FORM_STYLES.menuItem}>
                    {t("matrix.filter.range")}
                  </MenuItem>
                  <MenuItem value={FILTER_TYPES.LIST} sx={FORM_STYLES.menuItem}>
                    {t("matrix.filter.list")}
                  </MenuItem>
                </Select>
              </FormControl>
            </Tooltip>
          </Box>

          <TemporalFilterRenderer
            indexingType={rowFilter.indexingType}
            filterType={rowFilter.type}
            availableValues={availableValues}
            rangeValue={rangeValue}
            onRangeChange={handleRangeChange}
            selectedValues={rowFilter.list || []}
            onAddValue={handleAddValue}
            onRemoveValue={handleRemoveValue}
            onCheckboxChange={handleCheckbox}
            inputValue={inputValue}
            onInputChange={handleListChange}
            onKeyPress={handleKeyPress}
            onClearAll={handleClearAll}
            sliderMarks={sliderMarks}
          />
        </AccordionDetails>
      </Accordion>
    );
  },
);

RowFilterComponent.displayName = "RowFilterComponent";

export default RowFilterComponent;
