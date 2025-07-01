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

import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  type SelectChangeEvent,
  Typography,
} from "@mui/material";
import { memo, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { produce } from "immer";
import TemporalFilterRenderer from "./components/TemporalFilterRenderer";
import { FILTER_TYPES, TEMPORAL_OPTIONS, TIME_INDEXING } from "./constants";
import { useFilterControls } from "./hooks/useFilterControls";
import { useTemporalData } from "./hooks/useTemporalData";
import {
  ACCORDION_STYLES,
  CONTAINER_STYLES,
  DESIGN_TOKENS,
  FORM_STYLES,
  ICON_BUTTON_STYLES,
  TYPOGRAPHY_STYLES,
} from "./styles";
import type {
  FilterOperatorType,
  FilterType,
  RowFilterProps,
  RowFilter as RowFilterType,
  TimeIndexingType,
} from "./types";
import { createSliderMarks, getFilteredTemporalOptions } from "./utils";

const isValidTimeIndexingType = (value: string): value is TimeIndexingType => {
  return Object.values(TIME_INDEXING).includes(value as TimeIndexingType);
};

interface RowFilterState {
  rowFilter: RowFilterType;
  availableValues: { min: number; max: number; uniqueValues?: number[] };
  filteredOptions: typeof TEMPORAL_OPTIONS;
  rangeValue: [number, number];
  sliderMarks: Array<{ value: number; label: string }>;
  filterSummary: string;
}

function RowFilter({
  filter,
  setFilter,
  dateTime,
  isTimeSeries,
  timeFrequency,
  onRemoveFilter,
  filterId,
  expanded = true,
  onToggleExpanded,
}: RowFilterProps) {
  const { t } = useTranslation();

  const filterControls = useFilterControls({
    filter,
    setFilter,
    filterId,
  });

  const { valuesByIndexType } = useTemporalData({
    dateTime,
    isTimeSeries,
    timeFrequency,
  });

  const state = useMemo<RowFilterState>(() => {
    const rowFilter = filter.rowsFilters.find((rf) => rf.id === filterId) || filter.rowsFilters[0];

    const availableValues = valuesByIndexType[rowFilter.indexingType] || { min: 1, max: 100 };

    const rangeValue: [number, number] = [
      rowFilter.range?.min ?? availableValues.min,
      rowFilter.range?.max ?? availableValues.max,
    ];

    let filterSummary = "";
    if (filter.active) {
      const indexTypeLabel = t(`matrix.filter.indexing.${rowFilter.indexingType}`);

      if (rowFilter.type === FILTER_TYPES.RANGE && rowFilter.range) {
        filterSummary = ` (${indexTypeLabel}: ${rowFilter.range.min}-${rowFilter.range.max})`;
      } else if (rowFilter.type === FILTER_TYPES.LIST && rowFilter.list?.length) {
        const displayItems =
          rowFilter.list.length > 3
            ? `${rowFilter.list.slice(0, 3).join(", ")}...`
            : rowFilter.list.join(", ");

        filterSummary = ` ${indexTypeLabel}: [${displayItems}]`;
      }
    }

    return {
      rowFilter,
      availableValues,
      filteredOptions: getFilteredTemporalOptions(timeFrequency, [...TEMPORAL_OPTIONS]),
      rangeValue,
      sliderMarks: createSliderMarks(rowFilter.indexingType, t),
      filterSummary,
    };
  }, [filter.rowsFilters, filterId, valuesByIndexType, timeFrequency, t, filter.active]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onRemoveFilter?.(state.rowFilter.id);
    },
    [onRemoveFilter, state.rowFilter.id],
  );

  const handleAccordionChange = useCallback(() => {
    onToggleExpanded?.(state.rowFilter.id);
  }, [onToggleExpanded, state.rowFilter.id]);

  const handleIndexingTypeChange = useCallback(
    (e: SelectChangeEvent) => {
      const newType = e.target.value;

      if (isValidTimeIndexingType(newType)) {
        const newAvailableValues = valuesByIndexType[newType] || { min: 1, max: 100 };

        setFilter(
          produce((draft) => {
            const rowFilter = draft.rowsFilters.find((rf) => rf.id === state.rowFilter.id);

            if (rowFilter) {
              rowFilter.indexingType = newType;
              rowFilter.range = {
                min: newAvailableValues.min,
                max: newAvailableValues.max,
              };
              rowFilter.list = [];
            }
          }),
        );
      }
    },
    [valuesByIndexType, setFilter, state.rowFilter.id],
  );

  const handleTypeChange = useCallback(
    (e: SelectChangeEvent) => {
      filterControls.handleTypeChange(e.target.value as FilterType, filterId);
    },
    [filterControls, filterId],
  );

  const handleOperatorChange = useCallback(
    (operator: FilterOperatorType) => {
      filterControls.handleOperatorChange(operator, filterId);
    },
    [filterControls, filterId],
  );

  const handleRangeChange = useCallback(
    (newValues: [number, number]) => {
      setFilter(
        produce((draft) => {
          const currentFilter = draft.rowsFilters.find((rf) => rf.id === filterId);

          // Skip if the filter is not found or the range is the same
          if (
            !currentFilter ||
            (currentFilter.range?.min === newValues[0] && currentFilter.range?.max === newValues[1])
          ) {
            return;
          }

          currentFilter.range = { min: newValues[0], max: newValues[1] };
        }),
      );
    },
    [filterId, setFilter],
  );

  const canRemove = onRemoveFilter && filter.rowsFilters.length > 1;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Accordion
      expanded={expanded}
      onChange={handleAccordionChange}
      slotProps={{ transition: { unmountOnExit: true } }}
      sx={{ mb: DESIGN_TOKENS.spacing.sm }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon fontSize="small" />}
        sx={ACCORDION_STYLES.summary}
        component="div" // Avoid the nested button DOM validation error
      >
        <Box sx={CONTAINER_STYLES.flexRow}>
          <Typography sx={TYPOGRAPHY_STYLES.sectionTitle}>
            {state.filterSummary || t("matrix.filter.rowsFilter")}
          </Typography>
        </Box>
        {canRemove && (
          <IconButton
            size="small"
            onClick={handleDeleteClick}
            sx={ICON_BUTTON_STYLES.extraSmall}
            aria-label={t("matrix.filter.removeFilter")}
          >
            <DeleteIcon fontSize="small" sx={{ width: 13, height: 13 }} />
          </IconButton>
        )}
      </AccordionSummary>

      <AccordionDetails sx={ACCORDION_STYLES.details}>
        <Box sx={FORM_STYLES.sideBySideContainer}>
          <FormControl size="small" sx={{ flex: 1, ...FORM_STYLES.sideBySideFormControl }}>
            <InputLabel>{t("matrix.filter.indexingType")}</InputLabel>
            <Select
              value={state.rowFilter.indexingType}
              label={t("matrix.filter.indexingType")}
              onChange={handleIndexingTypeChange}
              sx={FORM_STYLES.sideBySideFormControl}
            >
              {state.filteredOptions.map((option) => (
                <MenuItem key={option.value} value={option.value} sx={FORM_STYLES.menuItem}>
                  {t(`matrix.filter.indexing.${option.value}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ flex: 1, ...FORM_STYLES.sideBySideFormControl }}>
            <InputLabel>{t("matrix.filter.type")}</InputLabel>
            <Select
              value={state.rowFilter.type}
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
          indexingType={state.rowFilter.indexingType}
          filterType={state.rowFilter.type}
          availableValues={state.availableValues}
          rangeValue={state.rangeValue}
          onRangeChange={handleRangeChange}
          selectedValues={state.rowFilter.list || []}
          onAddValue={() => filterControls.addValueToList(filterId)}
          onAddValues={(values) => filterControls.addValuesToList(values, filterId)}
          onRemoveValue={(value) => filterControls.removeValueFromList(value, filterId)}
          onCheckboxChange={(value) => filterControls.handleCheckboxChange(value, filterId)}
          inputValue={filterControls.inputValue}
          onInputChange={filterControls.handleListChange}
          onKeyPress={filterControls.handleKeyPress}
          onClearAll={() => filterControls.clearAllValues(filterId)}
          sliderMarks={state.sliderMarks}
          operator={state.rowFilter.operator}
          onOperatorChange={handleOperatorChange}
        />
      </AccordionDetails>
    </Accordion>
  );
}

export default memo(RowFilter);
