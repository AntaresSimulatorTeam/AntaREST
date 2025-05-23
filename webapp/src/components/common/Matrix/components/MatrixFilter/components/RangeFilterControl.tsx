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
import { useMemo, useCallback, memo } from "react";

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

const RangeFilterControl = memo(
  ({
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
    // Extract values for dependency array to avoid complex expressions
    const valueMin = value[0];
    const valueMax = value[1];

    // Memoize the value array to prevent unnecessary re-renders
    const sliderValue = useMemo(() => [valueMin, valueMax], [valueMin, valueMax]);

    // Memoize formatted values
    const formattedMin = useMemo(() => (formatValue ? formatValue(min) : min), [formatValue, min]);
    const formattedMax = useMemo(() => (formatValue ? formatValue(max) : max), [formatValue, max]);

    // Memoize marks to prevent recreation
    const memoizedMarks = useMemo(() => marks, [marks]);

    const handleChange = useCallback(
      (_event: Event, newValue: number | number[]) => {
        if (Array.isArray(newValue)) {
          onChange([newValue[0], newValue[1]]);
        }
      },
      [onChange],
    );

    return (
      <Box sx={{ px: 2, pt: 3, pb: 1 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "flex", justifyContent: "space-between" }}
        >
          <span>{formattedMin}</span>
          <span>{formattedMax}</span>
        </Typography>
        <Slider
          value={sliderValue}
          onChange={handleChange}
          valueLabelDisplay="auto"
          valueLabelFormat={formatValue}
          min={minBound}
          max={maxBound}
          marks={memoizedMarks}
          step={1}
          sx={{ mt: 1 }}
          disabled={disabled}
        />
      </Box>
    );
  },
);

// Add display name
RangeFilterControl.displayName = "RangeFilterControl";

export default memo(RangeFilterControl);
