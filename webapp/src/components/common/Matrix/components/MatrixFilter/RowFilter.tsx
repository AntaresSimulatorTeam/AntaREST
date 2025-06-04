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
  type FilterOperatorType,
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
      addValuesToList,
      removeValueFromList,
      clearAllValues,
      handleKeyPress,
      handleCheckboxChange,
      handleTypeChange: handleFilterTypeChange,
      handleOperatorChange,
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
        operator: foundFilter.operator,
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

    const handleOperatorChangeEvent = useCallback(
      (operator: FilterOperatorType) => {
        handleOperatorChange(operator, filterId);
      },
      [handleOperatorChange, filterId],
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
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((value) => ({
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
        return [
          1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
        ].map((value) => ({
          value,
          label: value.toString(),
        }));
      }

      if (indexingType === TIME_INDEXING.DAY_OF_YEAR) {
        return [1, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365].map((value) => ({
          value,
          label: value.toString(),
        }));
      }

      if (indexingType === TIME_INDEXING.HOUR_YEAR) {
        return [
          { value: 1, label: "Jan" },
          { value: 744, label: "Feb" },
          { value: 1416, label: "Mar" },
          { value: 2160, label: "Apr" },
          { value: 2880, label: "May" },
          { value: 3624, label: "Jun" },
          { value: 4344, label: "Jul" },
          { value: 5088, label: "Aug" },
          { value: 5832, label: "Sep" },
          { value: 6552, label: "Oct" },
          { value: 7296, label: "Nov" },
          { value: 8016, label: "Dec" },
          { value: 8760, label: "Dec 31" },
        ];
      }

      if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
        return [1, 5, 10, 15, 20, 25, 31].map((value) => ({
          value,
          label: value.toString(),
        }));
      }

      if (indexingType === TIME_INDEXING.WEEK) {
        return [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 53].map((value) => ({
          value,
          label: value.toString(),
        }));
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
            <IconButton size="small" onClick={handleDeleteClick} sx={ICON_BUTTON_STYLES.extraSmall}>
              <DeleteIcon fontSize="small" sx={{ width: 13, height: 13 }} />
            </IconButton>
          )}
        </AccordionSummary>
        <AccordionDetails sx={ACCORDION_STYLES.details}>
          <Box sx={FORM_STYLES.sideBySideContainer}>
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
          </Box>

          <TemporalFilterRenderer
            indexingType={rowFilter.indexingType}
            filterType={rowFilter.type}
            availableValues={availableValues}
            rangeValue={rangeValue}
            onRangeChange={handleRangeChange}
            selectedValues={rowFilter.list || []}
            onAddValue={handleAddValue}
            onAddValues={(values) => addValuesToList(values, filterId)}
            onRemoveValue={handleRemoveValue}
            onCheckboxChange={handleCheckbox}
            inputValue={inputValue}
            onInputChange={handleListChange}
            onKeyPress={handleKeyPress}
            onClearAll={handleClearAll}
            sliderMarks={sliderMarks}
            operator={rowFilter.operator}
            onOperatorChange={handleOperatorChangeEvent}
          />
        </AccordionDetails>
      </Accordion>
    );
  },
);

RowFilterComponent.displayName = "RowFilterComponent";

export default RowFilterComponent;
