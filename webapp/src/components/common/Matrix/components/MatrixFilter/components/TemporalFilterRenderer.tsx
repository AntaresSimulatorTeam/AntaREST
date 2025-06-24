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

import { Box } from "@mui/material";
import { memo, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";

import { TIME_INDEXING } from "../constants";
import { DESIGN_TOKENS } from "../styles";
import type { FilterOperatorType } from "../types";
import { getLocalizedTimeLabels } from "../utils/dateUtils";
import ChipSelector from "./ChipSelector";
import ListFilterControl from "./ListFilterControl";
import RangeFilterControl from "./RangeFilterControl";

interface TemporalFilterRendererProps {
  indexingType: string;
  filterType: string;
  availableValues: {
    min: number;
    max: number;
    uniqueValues?: number[];
  };
  rangeValue: [number, number];
  onRangeChange: (newValue: [number, number]) => void;
  selectedValues: number[];
  onAddValue: () => void;
  onAddValues?: (values: number[]) => void;
  onRemoveValue: (value: number) => void;
  onCheckboxChange: (value: number) => void;
  onClearAll: () => void;
  inputValue: string;
  onInputChange: (value: string) => void;
  onKeyPress: (event: React.KeyboardEvent) => void;
  disabled?: boolean;
  sliderMarks?: Array<{ value: number; label: string }>;
  operator?: FilterOperatorType;
  onOperatorChange?: (operator: FilterOperatorType) => void;
}

function TemporalFilterRenderer({
  indexingType,
  filterType,
  availableValues,
  rangeValue,
  onRangeChange,
  selectedValues,
  onAddValue,
  onAddValues,
  onRemoveValue,
  onCheckboxChange,
  onClearAll,
  inputValue,
  onInputChange,
  onKeyPress,
  disabled = false,
  sliderMarks,
  operator,
  onOperatorChange,
}: TemporalFilterRendererProps) {
  const { t } = useTranslation();

  const handleChipChange = useCallback(
    (value: number, _isSelected: boolean) => {
      // Call onCheckboxChange regardless of isSelected state
      // as it handles the toggle logic internally
      onCheckboxChange(value);
    },
    [onCheckboxChange],
  );

  // Format hour of year as human-readable text (Jan 1, 5h)
  const formatHourOfYear = useMemo(() => {
    return (hour: number): string => {
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
      return `${months[monthIndex]} ${dayOfMonth}, ${hourOfDay + 1}h`;
    };
  }, []);

  // Create localized option lists for months, weekdays, etc.
  const localizedOptions = useMemo(() => {
    if (indexingType === TIME_INDEXING.WEEKDAY) {
      return getLocalizedTimeLabels("weekday", t);
    }
    if (indexingType === TIME_INDEXING.MONTH) {
      return getLocalizedTimeLabels("month", t);
    }
    return [];
  }, [indexingType, t]);

  // Day of month options (1-31)
  const dayOfMonthOptions = useMemo(() => {
    if (indexingType !== TIME_INDEXING.DAY_OF_MONTH) {
      return [];
    }
    return Array.from({ length: 31 }, (_, i) => ({
      value: i + 1,
      label: (i + 1).toString(),
    }));
  }, [indexingType]);

  // Decide which component to render based on indexing and filter types
  if (filterType === "range") {
    if (indexingType === TIME_INDEXING.HOUR_YEAR) {
      return (
        <Box sx={{ px: DESIGN_TOKENS.spacing.xl, pt: 3, pb: DESIGN_TOKENS.spacing.lg }}>
          <RangeFilterControl
            min={rangeValue[0]}
            max={rangeValue[1]}
            value={rangeValue}
            onChange={onRangeChange}
            minBound={availableValues.min}
            maxBound={availableValues.max}
            marks={sliderMarks}
            disabled={disabled}
            formatValue={formatHourOfYear}
          />
        </Box>
      );
    }

    return (
      <RangeFilterControl
        min={rangeValue[0]}
        max={rangeValue[1]}
        value={rangeValue}
        onChange={onRangeChange}
        minBound={availableValues.min}
        maxBound={availableValues.max}
        marks={sliderMarks}
        disabled={disabled}
      />
    );
  }

  if (filterType === "list") {
    // Weekday selector
    if (indexingType === TIME_INDEXING.WEEKDAY) {
      return (
        <ChipSelector
          title={t("matrix.filter.selectDays")}
          options={localizedOptions.map((item) => ({
            value: item.value,
            label: item.label,
          }))}
          selectedValues={selectedValues}
          onChange={handleChipChange}
          disabled={disabled}
        />
      );
    }

    // Month selector
    if (indexingType === TIME_INDEXING.MONTH) {
      return (
        <ChipSelector
          title={t("matrix.filter.selectMonths")}
          options={localizedOptions.map((item) => ({
            value: item.value,
            label: item.label,
          }))}
          selectedValues={selectedValues}
          onChange={handleChipChange}
          disabled={disabled}
        />
      );
    }

    // Day of month selector
    if (indexingType === TIME_INDEXING.DAY_OF_MONTH) {
      return (
        <ChipSelector
          title={t("matrix.filter.selectDays")}
          options={dayOfMonthOptions}
          selectedValues={selectedValues}
          onChange={handleChipChange}
          disabled={disabled}
          dense={true}
          size="small"
        />
      );
    }

    // Week selector
    if (indexingType === TIME_INDEXING.WEEK) {
      const weekOptions = Array.from({ length: 53 }, (_, i) => ({
        value: i + 1,
        label: `${t("global.time.weekShort")} ${i + 1}`,
      }));

      return (
        <ChipSelector
          title={t("matrix.filter.selectWeeks")}
          options={weekOptions}
          selectedValues={selectedValues}
          onChange={handleChipChange}
          disabled={disabled}
          dense={true}
          size="small"
        />
      );
    }

    // Default list control for other types
    return (
      <ListFilterControl
        inputValue={inputValue}
        selectedValues={selectedValues}
        operator={operator}
        onInputChange={onInputChange}
        onKeyPress={onKeyPress}
        onAddValue={onAddValue}
        onAddValues={onAddValues}
        onRemoveValue={onRemoveValue}
        onOperatorChange={onOperatorChange}
        onClearAll={onClearAll}
        disabled={disabled}
      />
    );
  }

  return null;
}

export default memo(TemporalFilterRenderer);
