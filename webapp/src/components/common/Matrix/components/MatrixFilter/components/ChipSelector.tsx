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

import { Box, Chip, Stack, Typography } from "@mui/material";
import { CHIP_SELECTOR_STYLES, DESIGN_TOKENS } from "../styles";

export interface ChipOption {
  value: number;
  label: string;
  shortLabel?: string;
}

interface ChipSelectorProps {
  options: ChipOption[];
  selectedValues: number[];
  onChange: (value: number) => void;
  title?: string;
  size?: "small" | "medium";
  color?: "primary" | "secondary" | "default" | "error" | "info" | "success" | "warning";
  variant?: "filled" | "outlined";
  dense?: boolean;
  disabled?: boolean;
  renderOption?: (option: ChipOption, isSelected: boolean) => React.ReactNode;
}

function ChipSelector({
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
}: ChipSelectorProps) {
  const handleChipClick = (value: number) => {
    if (!disabled) {
      onChange(value);
    }
  };

  return (
    <Box>
      {title && (
        <Typography sx={{ fontSize: DESIGN_TOKENS.fontSize.xs, mb: DESIGN_TOKENS.spacing.sm }}>
          {title}
        </Typography>
      )}
      <Stack
        direction="row"
        spacing={dense ? DESIGN_TOKENS.spacing.sm : DESIGN_TOKENS.spacing.lg}
        flexWrap="wrap"
        useFlexGap
        sx={dense ? { maxWidth: "100%" } : undefined}
      >
        {options.map((option) => {
          const isSelected = selectedValues.includes(option.value);

          if (renderOption) {
            return (
              <Box
                key={option.value}
                style={{
                  cursor: disabled ? "default" : "pointer",
                  opacity: disabled ? 0.7 : 1,
                }}
              >
                {renderOption(option, isSelected)}
              </Box>
            );
          }

          return (
            <Chip
              key={option.value}
              label={option.label}
              onClick={() => handleChipClick(option.value)}
              color={isSelected ? color : "default"}
              variant={isSelected ? "filled" : variant}
              size={size}
              disabled={disabled}
              sx={dense ? CHIP_SELECTOR_STYLES.dense : CHIP_SELECTOR_STYLES.normal}
            />
          );
        })}
      </Stack>
    </Box>
  );
}

export default ChipSelector;
