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

import LinearProgressWithLabel from "@/components/LinearProgressWithLabel";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getLauncherMetrics } from "@/services/api/study";
import { toError } from "@/utils/fnUtils";
import { Box, Paper, Skeleton, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useInterval } from "react-use";

interface ClustersMetricsBlockProps {
  launcherId: string;
  launcherName: string;
}

function ClustersMetricsBlock({ launcherId, launcherName }: ClustersMetricsBlockProps) {
  const { t } = useTranslation();

  const metricsRes = usePromiseWithSnackbarError(() => getLauncherMetrics(launcherId), {
    errorMessage: t("study.error.launchLoad"),
    deps: [launcherId],
  });

  // Refresh metrics every minute
  useInterval(metricsRes.reload, 60_000);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper
      elevation={0}
      sx={{
        p: 0.75,
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
        minWidth: 180,
        flex: "0 0 auto",
        border: 1,
        borderColor: "divider",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="caption" fontWeight="bold" sx={{ fontSize: "0.7rem" }}>
          {launcherName}
        </Typography>
        <UsePromiseCond
          key={launcherId}
          response={metricsRes}
          keepLastResolvedOnReload
          ifPending={() => <Skeleton width={40} height={14} />}
          ifRejected={() => null}
          ifFulfilled={(metrics) => (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <Typography variant="caption" sx={{ fontSize: "0.65rem" }}>
                {t("study.nbQueuedJobs")}:
              </Typography>
              <Typography variant="caption" fontWeight="bold" sx={{ fontSize: "0.7rem" }}>
                {metrics.nbQueuedJobs}
              </Typography>
            </Box>
          )}
        />
      </Box>
      <UsePromiseCond
        key={launcherId}
        response={metricsRes}
        keepLastResolvedOnReload
        ifPending={() => (
          <>
            <Skeleton width="100%" height={16} />
            <Skeleton width="100%" height={16} />
          </>
        )}
        ifRejected={(err) => (
          <Typography color="error" variant="caption" sx={{ fontSize: "0.65rem" }}>
            {toError(err).message}
          </Typography>
        )}
        ifFulfilled={(metrics) => (
          <>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <Typography
                variant="caption"
                sx={{ textWrap: "nowrap", fontSize: "0.65rem", minWidth: 50 }}
              >
                {t("study.allocatedCpuRate")}
              </Typography>
              <LinearProgressWithLabel
                value={Math.floor(metrics.allocatedCpuRate)}
                tooltip={t("study.allocatedCpuRate")}
                colorMode="cluster"
                sx={{ height: 16, flex: 1 }}
              />
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <Typography
                variant="caption"
                sx={{ textWrap: "nowrap", fontSize: "0.65rem", minWidth: 50 }}
              >
                {t("study.clusterLoadRate")}
              </Typography>
              <LinearProgressWithLabel
                value={Math.floor(metrics.clusterLoadRate)}
                tooltip={t("study.clusterLoadRate")}
                colorMode="cluster"
                sx={{ height: 16, flex: 1 }}
              />
            </Box>
          </>
        )}
      />
    </Paper>
  );
}

export default ClustersMetricsBlock;
