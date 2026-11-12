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

import { filesystemQueries } from "@/queries/filesystem/queries";
import { formatBytes } from "@/utils/byteUtils";
import { getUsageColor } from "@/theme/utils";
import { Box, LinearProgress, Tooltip, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { indicatorStyles, percentageStyles, progressStyles } from "./styles";

interface Props {
  workspace: string;
  label: string;
}

function DiskUsageIndicator({ workspace, label }: Props) {
  const { t, i18n } = useTranslation();
  const { data, isError } = useQuery(filesystemQueries.workspaceDiskUsage(workspace));

  const locale = i18n.resolvedLanguage ?? i18n.language;

  const { percentage, color, formattedPercentage, tooltip } = useMemo(() => {
    if (!data) {
      return {
        percentage: 0,
        color: "inherit",
        formattedPercentage: "—",
        tooltip: t(isError ? "studies.tree.diskUsage.unavailable" : "global.loading"),
      } as const;
    }

    const { usedBytes, totalBytes, freeBytes } = data;
    const percentage = Math.min((usedBytes / totalBytes) * 100, 100);

    return {
      percentage,
      color: getUsageColor(percentage),
      formattedPercentage: (percentage / 100).toLocaleString(locale, {
        style: "percent",
        maximumFractionDigits: 0,
      }),
      tooltip: t("studies.tree.diskUsage.details", {
        available: formatBytes(freeBytes),
        total: formatBytes(totalBytes),
      }),
    } as const;
  }, [data, isError, locale, t]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip title={tooltip} placement="bottom" describeChild arrow>
      <Box tabIndex={0} role="group" aria-label={label} sx={indicatorStyles}>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={color}
          aria-label={label}
          aria-hidden={!data}
          sx={progressStyles}
        />
        <Typography component="span" variant="caption" color={color} sx={percentageStyles}>
          {formattedPercentage}
        </Typography>
      </Box>
    </Tooltip>
  );
}

export default DiskUsageIndicator;
