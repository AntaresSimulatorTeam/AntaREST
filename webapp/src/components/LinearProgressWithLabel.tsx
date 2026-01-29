/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import InfoIcon from "@mui/icons-material/Info";
import {
  Box,
  LinearProgress,
  type LinearProgressProps,
  type SxProps,
  type Theme,
  Tooltip,
  Typography,
} from "@mui/material";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { mergeSxProp } from "@/utils/muiUtils";

/**
 * Determines the color of the progress bar based on value and mode
 *
 * @param value - Progress value (0-100)
 * @param error - Whether there's an error state
 * @param colorMode - Color mode: "default" for standard behavior, "cluster" for cluster computing indicators
 * @returns Material-UI color variant
 */
function getColor(value = 0, error = false, colorMode: "default" | "cluster" = "default") {
  if (error) {
    return "error";
  }

  if (colorMode === "cluster") {
    // Cluster computing indicators: high usage = bad
    if (value >= 90) {
      return "error"; // Red for ≥ 90% (critical usage)
    }
    if (value > 50) {
      return "warning"; // Orange for > 50% and < 90% (moderate usage)
    }
    return "success"; // Green for ≤ 50% (safe usage)
  }

  // Default behavior: maintains backward compatibility for other use cases
  if (value === 100) {
    return "success";
  }
  return "primary";
}

interface LinearProgressWithLabelProps {
  value?: LinearProgressProps["value"];
  tooltip?: string;
  error?: boolean | string;
  sx?: SxProps<Theme>;
  /**
   * Color mode for the progress bar:
   * - "default": Standard behavior (green at 100%, blue for progress)
   * - "cluster": Cluster computing indicators (red ≥90%, orange 50-90%, green ≤50%)
   */
  colorMode?: "default" | "cluster";
}

function LinearProgressWithLabel({
  value,
  tooltip,
  error,
  sx,
  colorMode = "default",
}: LinearProgressWithLabelProps) {
  const progress = R.clamp(0, 100, value || 0);
  const hasError = error === true || typeof error === "string";
  const variant = typeof value === "number" || hasError ? "determinate" : "indeterminate";

  const { t } = useTranslation();

  const content = (
    <Box sx={mergeSxProp({ display: "flex", alignItems: "center", height: 22 }, sx)}>
      <Box sx={{ width: "100%", mr: 1 }}>
        <LinearProgress
          value={progress}
          variant={variant}
          color={getColor(value, hasError, colorMode)}
        />
      </Box>
      {variant === "determinate" && (
        <Box sx={{ minWidth: 35, display: "flex", gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {`${Math.round(progress)}%`}
          </Typography>
          {typeof error === "string" && (
            <Tooltip title={error || t("global.error")} placement="top">
              <InfoIcon fontSize="small" />
            </Tooltip>
          )}
        </Box>
      )}
    </Box>
  );

  return tooltip ? <Tooltip title={tooltip}>{content}</Tooltip> : content;
}

export default LinearProgressWithLabel;
