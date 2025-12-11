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

import CustomScrollbar from "@/components/CustomScrollbar";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getLaunchersConfig } from "@/services/api/launcher/index";
import { toError } from "@/utils/fnUtils";
import { Box, Skeleton, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import ClustersMetricsBlock from "./ClustersMetricsBlock";

function ClustersMetrics() {
  const { t } = useTranslation();

  const launchersConfigRes = usePromiseWithSnackbarError(getLaunchersConfig, {
    errorMessage: t("study.error.launchLoad"),
    deps: [],
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <CustomScrollbar>
      <Box
        sx={{
          display: "flex",
          gap: 1,
        }}
      >
        <UsePromiseCond
          response={launchersConfigRes}
          ifPending={() => (
            <>
              <Skeleton variant="rectangular" width={180} height={60} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={180} height={60} sx={{ borderRadius: 1 }} />
            </>
          )}
          ifRejected={(err) => (
            <Typography color="error">
              {t("study.error.launchLoad")}: {toError(err).message}
            </Typography>
          )}
          ifFulfilled={({ launchers }) => (
            <>
              {launchers.map((launcher) => (
                <ClustersMetricsBlock
                  key={launcher.id}
                  launcherId={launcher.id}
                  launcherName={launcher.name}
                />
              ))}
            </>
          )}
        />
      </Box>
    </CustomScrollbar>
  );
}

export default ClustersMetrics;
