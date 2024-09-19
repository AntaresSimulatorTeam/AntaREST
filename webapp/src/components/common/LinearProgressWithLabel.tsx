/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
  Tooltip,
  Box,
  LinearProgress,
  Typography,
  LinearProgressProps,
} from "@mui/material";
import * as R from "ramda";

const renderLoadColor = (val: number): LinearProgressProps["color"] =>
  R.cond([
    [(v: number) => v > 90, () => "error" as const],
    [(v: number) => v > 75, () => "primary" as const],
    [R.T, () => "success" as const],
  ])(val);

interface PropsType {
  indicator: number;
  size?: string;
  tooltip: string;
  gradiant?: boolean;
}

function LinearProgressWithLabel(props: PropsType) {
  const { indicator, size = "100%", tooltip, gradiant = false } = props;

  return (
    <Tooltip title={tooltip}>
      <Box sx={{ display: "flex", alignItems: "center", width: size }}>
        <Box sx={{ width: "100%", mr: 1 }}>
          <LinearProgress
            color={gradiant ? renderLoadColor(indicator) : "inherit"}
            variant="determinate"
            value={indicator > 100 ? 100 : indicator}
          />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">{`${Math.round(
            indicator || 0,
          )}%`}</Typography>
        </Box>
      </Box>
    </Tooltip>
  );
}

export default LinearProgressWithLabel;
