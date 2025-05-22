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

const ChipSelector = ({
  options,
  selectedValues,
  onChange,
  title,
  size = "small",
  color = "primary",
  variant = "outlined",
  dense = false,
  disabled = false,
  renderOption,
}: ChipSelectorProps) => {
  const handleChipClick = (value: number) => {
    if (!disabled) {
      onChange(value);
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      {title && (
        <Typography variant="subtitle2" gutterBottom>
          {title}
        </Typography>
      )}
      <Stack
        direction="row"
        spacing={dense ? 0.5 : 1}
        flexWrap="wrap"
        useFlexGap
        sx={dense ? { maxWidth: "100%" } : undefined}
      >
        {options.map((option) => {
          const isSelected = selectedValues.includes(option.value);

          if (renderOption) {
            // Use a div instead of Box with onClick to prevent button nesting issues
            // when renderOption returns a button-like element
            return (
              <div
                key={option.value}
                style={{
                  cursor: disabled ? "default" : "pointer",
                  opacity: disabled ? 0.7 : 1,
                }}
              >
                {renderOption(option, isSelected)}
              </div>
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
              sx={dense ? { m: 0.2, minWidth: 36, height: 24 } : { my: 0.5 }}
            />
          );
        })}
      </Stack>
    </Box>
  );
};

export default ChipSelector;
