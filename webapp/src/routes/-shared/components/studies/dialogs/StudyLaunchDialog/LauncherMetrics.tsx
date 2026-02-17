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
import { Box, Skeleton, Typography } from "@mui/material";
import { useFormContext, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useInterval } from "react-use";
import type { FormValues } from "./utils";

function LauncherMetrics() {
  const { t } = useTranslation();
  const { control } = useFormContext<FormValues>();
  const currentLauncherId = useWatch({ control, name: "launcher" });

  const launcherMetricsRes = usePromiseWithSnackbarError(
    () => getLauncherMetrics(currentLauncherId || undefined),
    {
      errorMessage: t("study.error.launchLoad"),
      deps: [currentLauncherId],
    },
  );

  // Refresh launcher metrics every minute
  useInterval(launcherMetricsRes.reload, 60_000);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        alignContent: "center",
        gap: 1,
      }}
    >
      <UsePromiseCond
        // Reload when launcher changes to see Skeleton
        // because `keepLastResolvedOnReload` is set to true for refresh
        key={currentLauncherId}
        response={launcherMetricsRes}
        keepLastResolvedOnReload
        ifPending={() => (
          <>
            <Skeleton width={150} />
            <Skeleton width={150} />
            <Skeleton width={150} />
          </>
        )}
        ifRejected={(err) => (
          <>
            <Typography sx={{ flexBasis: "100%" }}>{t("study.error.launchLoad")}</Typography>
            <Typography>{toError(err).message}</Typography>
          </>
        )}
        ifFulfilled={(metrics) => (
          <>
            <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
              {t("study.allocatedCpuRate")}
            </Typography>
            <LinearProgressWithLabel
              value={Math.floor(metrics.allocatedCpuRate)}
              tooltip={t("study.allocatedCpuRate")}
              sx={{ width: 100 }}
              colorMode="cluster"
            />
            <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
              {t("study.clusterLoadRate")}
            </Typography>
            <LinearProgressWithLabel
              value={Math.floor(metrics.clusterLoadRate)}
              tooltip={t("study.clusterLoadRate")}
              sx={{ width: 100 }}
              colorMode="cluster"
            />
            <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
              {t("study.nbQueuedJobs")}: {metrics.nbQueuedJobs}
            </Typography>
          </>
        )}
      />
    </Box>
  );
}

export default LauncherMetrics;
