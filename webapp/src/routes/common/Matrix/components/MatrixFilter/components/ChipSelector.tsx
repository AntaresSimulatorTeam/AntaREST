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

import { Box, Chip, type ChipProps, Stack, Typography } from "@mui/material";
import { memo, useCallback, useMemo } from "react";
import { CHIP_SELECTOR_STYLES, DESIGN_TOKENS } from "../styles";

export interface ChipOption<T extends string | number = number> {
  value: T;
  label: string;
  shortLabel?: string;
  disabled?: boolean;
}

interface ChipSelectorProps<T extends string | number = number> {
  options: ReadonlyArray<ChipOption<T>>;
  selectedValues: readonly T[];
  onChange: (value: T, isSelected: boolean) => void;
  title?: string;
  size?: ChipProps["size"];
  color?: ChipProps["color"];
  variant?: ChipProps["variant"];
  dense?: boolean;
  disabled?: boolean;
  renderOption?: (option: ChipOption<T>, isSelected: boolean) => React.ReactNode;
  "aria-label"?: string;
  multiple?: boolean;
}

function ChipSelectorComponent<T extends string | number = number>({
  options,
  selectedValues,
  onChange,
  title,
  size = "small",
  color = "primary",
  variant = "outlined",
  dense = true,
  disabled = false,
  renderOption,
  "aria-label": ariaLabel,
  multiple = true,
}: ChipSelectorProps<T>) {
  const selectedSet = useMemo(() => new Set(selectedValues), [selectedValues]);

  const handleChipClick = useCallback(
    (value: T) => {
      if (!disabled) {
        const isSelected = selectedSet.has(value);
        onChange(value, !isSelected);
      }
    },
    [disabled, selectedSet, onChange],
  );

  const containerStyles = useMemo(
    () => ({
      ...(dense ? { maxWidth: "100%" } : undefined),
    }),
    [dense],
  );

  const spacing = dense ? DESIGN_TOKENS.spacing.sm : DESIGN_TOKENS.spacing.lg;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box role={multiple ? "group" : "radiogroup"} aria-label={ariaLabel || title}>
      {title && (
        <Typography
          component="h3"
          sx={{
            fontSize: DESIGN_TOKENS.fontSize.xs,
            mb: DESIGN_TOKENS.spacing.sm,
          }}
        >
          {title}
        </Typography>
      )}
      <Stack direction="row" spacing={spacing} flexWrap="wrap" useFlexGap sx={containerStyles}>
        {options.map((option) => {
          const isSelected = selectedSet.has(option.value);
          const isOptionDisabled = disabled || option.disabled;

          if (renderOption) {
            return (
              <Box
                key={String(option.value)}
                onClick={() => !isOptionDisabled && handleChipClick(option.value)}
                sx={{
                  cursor: isOptionDisabled ? "default" : "pointer",
                  opacity: isOptionDisabled ? 0.7 : 1,
                  transition: "opacity 0.2s",
                  userSelect: "none",
                }}
                role={multiple ? "checkbox" : "radio"}
                aria-checked={isSelected}
                aria-disabled={isOptionDisabled}
                tabIndex={isOptionDisabled ? -1 : 0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    if (!isOptionDisabled) {
                      handleChipClick(option.value);
                    }
                  }
                }}
              >
                {renderOption(option, isSelected)}
              </Box>
            );
          }

          return (
            <Chip
              key={String(option.value)}
              label={option.shortLabel || option.label}
              onClick={() => handleChipClick(option.value)}
              color={isSelected ? color : "default"}
              variant={isSelected ? "filled" : variant}
              size={size}
              disabled={isOptionDisabled}
              sx={dense ? CHIP_SELECTOR_STYLES.dense : CHIP_SELECTOR_STYLES.normal}
              aria-pressed={isSelected}
              role={multiple ? "checkbox" : "radio"}
              aria-checked={isSelected}
            />
          );
        })}
      </Stack>
    </Box>
  );
}

export default memo(ChipSelectorComponent) as <T extends string | number = number>(
  props: ChipSelectorProps<T>,
) => React.ReactElement;
