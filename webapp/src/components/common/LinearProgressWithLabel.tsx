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
  type LinearProgressProps,
  type SxProps,
  type Theme,
} from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import * as R from "ramda";
import { mergeSxProp } from "@/utils/muiUtils";
import { useTranslation } from "react-i18next";

function getColor(value = 0, error = false) {
  if (error) {
    return "error";
  }
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
}

function LinearProgressWithLabel(props: LinearProgressWithLabelProps) {
  const { value, tooltip, error, sx } = props;
  const progress = R.clamp(0, 100, value || 0);
  const hasError = error === true || typeof error === "string";
  const variant =
    typeof value === "number" || hasError ? "determinate" : "indeterminate";

  const { t } = useTranslation();

  const content = (
    <Box
      sx={mergeSxProp(
        { display: "flex", alignItems: "center", height: 22 },
        sx,
      )}
    >
      <Box sx={{ width: "100%", mr: 1 }}>
        <LinearProgress
          value={progress}
          variant={variant}
          color={getColor(value, hasError)}
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
