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
  TextField,
  Box,
  Typography,
  Chip,
  InputAdornment,
  IconButton,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  type SelectChangeEvent,
} from "@mui/material";
import ClearIcon from "@mui/icons-material/Clear";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useTranslation } from "react-i18next";
import { useMemo } from "react";
import {
  CHIP_SELECTOR_STYLES,
  DESIGN_TOKENS,
  FORM_STYLES,
  ICON_BUTTON_STYLES,
  TYPOGRAPHY_STYLES,
} from "../styles";
import { FILTER_OPERATORS, type FilterOperatorType } from "../constants";

interface ListFilterControlProps {
  inputValue: string;
  selectedValues: number[];
  operator?: FilterOperatorType;
  onInputChange: (value: string) => void;
  onKeyPress: (event: React.KeyboardEvent) => void;
  onAddValue: () => void;
  onAddValues?: (values: number[]) => void;
  onRemoveValue: (value: number) => void;
  onOperatorChange?: (operator: FilterOperatorType) => void;
  onClearAll?: () => void;
  placeholder?: string;
  disabled?: boolean;
}

function ListFilterControl({
  inputValue,
  selectedValues,
  operator = FILTER_OPERATORS.EQUALS,
  onInputChange,
  onKeyPress,
  onAddValue,
  onAddValues,
  onOperatorChange,
  onClearAll,
  placeholder,
  disabled = false,
}: ListFilterControlProps) {
  const { t } = useTranslation();

  // Format selected values as ranges (e.g., "1-5, 7, 10-15")
  const formattedValues = useMemo(() => {
    if (selectedValues.length === 0) {
      return "";
    }

    const sorted = [...selectedValues].sort((a, b) => a - b);

    const formatRange = (start: number, end: number): string => {
      if (start === end) {
        return start.toString();
      }

      if (end === start + 1) {
        return `${start}, ${end}`;
      }

      return `${start}-${end}`;
    };

    const ranges = sorted.reduce<Array<[number, number]>>((acc, curr, idx) => {
      if (idx === 0) {
        return [[curr, curr]];
      }

      const lastRange = acc[acc.length - 1];
      const [, lastEnd] = lastRange;

      if (curr === lastEnd + 1) {
        // Extend the current range
        lastRange[1] = curr;
      } else {
        // Start a new range
        acc.push([curr, curr]);
      }

      return acc;
    }, []);

    return ranges.map(([start, end]) => formatRange(start, end)).join(", ");
  }, [selectedValues]);

  const handleOperatorChange = (e: SelectChangeEvent) => {
    if (onOperatorChange) {
      onOperatorChange(e.target.value as FilterOperatorType);
    }
  };

  const parseRangeInput = (input: string): number[] => {
    const trimmed = input.trim();

    // Check if input contains a range (e.g., "8-100", "5 - 10")
    const rangeMatch = trimmed.match(/^(\d+)\s*-\s*(\d+)$/);
    if (rangeMatch) {
      const start = Number.parseInt(rangeMatch[1], 10);
      const end = Number.parseInt(rangeMatch[2], 10);
      if (!Number.isNaN(start) && !Number.isNaN(end) && start <= end) {
        return Array.from({ length: end - start + 1 }, (_, i) => start + i);
      }
    }

    // Check for comma-separated values
    const values = trimmed
      .split(",")
      .map((v) => {
        const num = Number.parseInt(v.trim(), 10);
        return Number.isNaN(num) ? null : num;
      })
      .filter((v) => v !== null) as number[];

    return values;
  };

  const handleAddValue = () => {
    const values = parseRangeInput(inputValue);
    if (values.length > 1 && onAddValues) {
      // Use onAddValues for multiple values (ranges)
      const newValues = values.filter((value) => !selectedValues.includes(value));
      if (newValues.length > 0) {
        onAddValues(newValues);
        onInputChange("");
      }
    } else if (values.length === 1) {
      // Use onAddValue for single values
      onAddValue();
    } else {
      // Fallback to onAddValue for invalid input
      onAddValue();
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      handleAddValue();
    } else {
      onKeyPress(event);
    }
  };

  return (
    <>
      <Box sx={{ ...FORM_STYLES.sideBySideContainer }}>
        <Box sx={FORM_STYLES.responsiveContainer}>
          {onOperatorChange && (
            <FormControl size="small" sx={FORM_STYLES.sideBySideFormControl}>
              <InputLabel>{t("matrix.filter.operator.label")}</InputLabel>
              <Select
                value={operator}
                label={t("matrix.filter.operator.label")}
                onChange={handleOperatorChange}
                disabled={disabled}
                sx={FORM_STYLES.sideBySideFormControl}
              >
                <MenuItem value={FILTER_OPERATORS.EQUALS} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.equals")}
                </MenuItem>
                <MenuItem value={FILTER_OPERATORS.GREATER_THAN} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.greaterThan")}
                </MenuItem>
                <MenuItem value={FILTER_OPERATORS.LESS_THAN} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.lessThan")}
                </MenuItem>
                <MenuItem value={FILTER_OPERATORS.GREATER_EQUAL} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.greaterEqual")}
                </MenuItem>
                <MenuItem value={FILTER_OPERATORS.LESS_EQUAL} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.lessEqual")}
                </MenuItem>
                <MenuItem value={FILTER_OPERATORS.RANGE} sx={FORM_STYLES.menuItem}>
                  {t("matrix.filter.operator.range")}
                </MenuItem>
              </Select>
            </FormControl>
          )}

          <Box sx={{ flex: 1 }}>
            <TextField
              label={t("matrix.filter.listValues")}
              placeholder={placeholder || t("matrix.filter.enterValue")}
              size="small"
              value={inputValue}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyPress}
              type="text"
              disabled={disabled}
              sx={FORM_STYLES.textField}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <Tooltip title={t("matrix.filter.listTooltip")} arrow placement="top">
                        <IconButton
                          size="small"
                          edge="end"
                          disabled={disabled}
                          sx={ICON_BUTTON_STYLES.extraSmall}
                        >
                          <InfoOutlinedIcon fontSize="small" sx={{ width: 13, height: 13 }} />
                        </IconButton>
                      </Tooltip>
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Box>
        </Box>
      </Box>

      {selectedValues.length > 0 && (
        <Box sx={{ mt: DESIGN_TOKENS.spacing.sm }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: DESIGN_TOKENS.spacing.sm,
            }}
          >
            <Typography color="text.secondary" sx={TYPOGRAPHY_STYLES.smallCaption}>
              {t("matrix.filter.selectedValues")} ({selectedValues.length}):
            </Typography>
            {onClearAll && (
              <Button
                variant="text"
                size="small"
                startIcon={<ClearIcon fontSize="small" />}
                onClick={onClearAll}
                disabled={disabled}
                sx={{
                  minWidth: "auto",
                  fontSize: DESIGN_TOKENS.fontSize.xs,
                  py: DESIGN_TOKENS.spacing.xs,
                  px: DESIGN_TOKENS.spacing.sm,
                  height: 20,
                }}
              >
                {t("matrix.filter.clearAll")}
              </Button>
            )}
          </Box>
          <Chip
            label={formattedValues}
            size="small"
            color="primary"
            disabled={disabled}
            sx={CHIP_SELECTOR_STYLES.dense}
          />
        </Box>
      )}
    </>
  );
}

export default ListFilterControl;
