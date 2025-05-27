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

import { useMemo, memo } from "react";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { TIME_INDEXING } from "../constants";
import { getLocalizedTimeLabels } from "../dateUtils";
import { DESIGN_TOKENS } from "../styles";
import RangeFilterControl from "./RangeFilterControl";
import ListFilterControl from "./ListFilterControl";
import ChipSelector from "./ChipSelector";

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
  onRemoveValue: (value: number) => void;
  onCheckboxChange: (value: number) => void;
  onClearAll: () => void;
  inputValue: string;
  onInputChange: (value: string) => void;
  onKeyPress: (event: React.KeyboardEvent) => void;
  disabled?: boolean;
  sliderMarks?: Array<{ value: number; label: string }>;
}

const TemporalFilterRenderer = memo(
  ({
    indexingType,
    filterType,
    availableValues,
    rangeValue,
    onRangeChange,
    selectedValues,
    onAddValue,
    onRemoveValue,
    onCheckboxChange,
    onClearAll,
    inputValue,
    onInputChange,
    onKeyPress,
    disabled = false,
    sliderMarks,
  }: TemporalFilterRendererProps) => {
    const { t } = useTranslation();

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
        return `${months[monthIndex]} ${dayOfMonth}, ${hourOfDay}h`;
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

    // Create common time period options for hour of year
    const hourOfYearOptions = useMemo(() => {
      if (indexingType !== TIME_INDEXING.HOUR_YEAR) {
        return [];
      }
      return [
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
    }, [indexingType]);

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

    // Memoize formatted range values for hour of year
    const formattedRange = useMemo(() => {
      if (indexingType === TIME_INDEXING.HOUR_YEAR) {
        return {
          min: formatHourOfYear(rangeValue[0]),
          max: formatHourOfYear(rangeValue[1]),
        };
      }
      return null;
    }, [indexingType, rangeValue, formatHourOfYear]);

    // Decide which component to render based on indexing and filter types
    if (filterType === "range") {
      if (indexingType === TIME_INDEXING.HOUR_YEAR) {
        return (
          <Box sx={{ px: DESIGN_TOKENS.spacing.xl, pt: 3, pb: DESIGN_TOKENS.spacing.lg }}>
            <Box sx={{ mb: DESIGN_TOKENS.spacing.xl }}>
              <Typography variant="caption" color="text.secondary">
                Hour of year range:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: "medium" }}>
                {formattedRange?.min} - {formattedRange?.max}
              </Typography>
            </Box>

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
      // Special handling for hour of year
      if (indexingType === TIME_INDEXING.HOUR_YEAR) {
        return (
          <Box sx={{ mt: DESIGN_TOKENS.spacing.xl }}>
            <ChipSelector
              title={t("matrix.filter.commonTimePeriods")}
              options={hourOfYearOptions}
              selectedValues={selectedValues}
              onChange={onCheckboxChange}
              disabled={disabled}
            />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: DESIGN_TOKENS.spacing.xl, mb: DESIGN_TOKENS.spacing.lg }}
            >
              Or add specific hours manually:
            </Typography>

            <ListFilterControl
              inputValue={inputValue}
              selectedValues={selectedValues}
              onInputChange={onInputChange}
              onKeyPress={onKeyPress}
              onAddValue={onAddValue}
              onRemoveValue={onRemoveValue}
              onClearAll={onClearAll}
              placeholder="Enter hour number (1-8760)"
              disabled={disabled}
            />
          </Box>
        );
      }

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
            onChange={onCheckboxChange}
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
            onChange={onCheckboxChange}
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
            onChange={onCheckboxChange}
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
          onInputChange={onInputChange}
          onKeyPress={onKeyPress}
          onAddValue={onAddValue}
          onRemoveValue={onRemoveValue}
          onClearAll={onClearAll}
          disabled={disabled}
        />
      );
    }

    return null;
  },
);

// Add display name for debugging
TemporalFilterRenderer.displayName = "TemporalFilterRenderer";

export default TemporalFilterRenderer;
