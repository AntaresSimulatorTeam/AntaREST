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

import { Box, Typography, Slider } from "@mui/material";

interface RangeFilterControlProps {
  min: number;
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
  minBound: number;
  maxBound: number;
  marks?: Array<{ value: number; label: string }>;
  disabled?: boolean;
  formatValue?: (value: number) => string;
}

const RangeFilterControl = ({
  min,
  max,
  value,
  onChange,
  minBound,
  maxBound,
  marks,
  disabled = false,
  formatValue,
}: RangeFilterControlProps) => {
  const handleChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      onChange([newValue[0], newValue[1]]);
    }
  };

  return (
    <Box sx={{ px: 2, pt: 3, pb: 1 }}>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "flex", justifyContent: "space-between" }}
      >
        <span>{formatValue ? formatValue(min) : min}</span>
        <span>{formatValue ? formatValue(max) : max}</span>
      </Typography>
      <Slider
        value={[value[0], value[1]]}
        onChange={handleChange}
        valueLabelDisplay="auto"
        valueLabelFormat={formatValue}
        min={minBound}
        max={maxBound}
        marks={marks}
        step={1}
        sx={{ mt: 1 }}
        disabled={disabled}
      />
    </Box>
  );
};

export default RangeFilterControl;
