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

import { jobKeys } from "@/queries/jobs/keys";
import { jobQueries } from "@/queries/jobs/queries";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { addWsEventListener, subscribeWsChannels } from "@/services/webSocket/ws";
import type { JobsProgressById } from "@/types/types";
import HistoryIcon from "@mui/icons-material/History";
import { Paper, Stack, Typography } from "@mui/material";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAsync } from "react-use";
import useStudy from "../../../-hooks/useStudy";
import JobStepper from "./JobStepper";
import { getJobsProgressById, sortJobs } from "./utils";

function LauncherHistory() {
  const { t } = useTranslation();
  const [jobsProgressById, setJobsProgressById] = useState<JobsProgressById>({});
  const study = useStudy();
  const queryClient = useQueryClient();

  const { data: jobs } = useSuspenseQuery({
    ...jobQueries.list(study.id),
    select: sortJobs,
  });

  // Update jobs progress on mount and when jobs change
  useAsync(async () => {
    setJobsProgressById(await getJobsProgressById(jobs));
  }, [jobs]);

  // Listen to job-related WebSocket events to keep the jobs list and progress up to date
  useEffect(() => {
    const listener = (event: WsEvent) => {
      if (
        event.type === WsEventType.StudyJobStarted ||
        event.type === WsEventType.StudyJobStatusUpdate ||
        event.type === WsEventType.StudyJobCompleted
      ) {
        if (event.payload.study_id === study.id) {
          queryClient.invalidateQueries({ queryKey: jobKeys.list(study.id) });
        }
      } else if (event.type === WsEventType.LaunchProgress) {
        const message = event.payload;
        setJobsProgressById((prev) => ({ ...prev, [message.id]: message.progress }));
      }
    };

    return addWsEventListener(listener);
  }, [queryClient, study.id]);

  // Subscribe to job-related WebSocket channels to receive real-time updates
  useEffect(() => {
    const channels = jobs.map((job) => WsChannel.JobStatus + job.id);
    return subscribeWsChannels(channels);
  }, [jobs]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack component={Paper} direction="column" sx={{ height: 1, p: 1, flex: 1.5 }} elevation={2}>
      <Typography
        color="text.secondary"
        sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
      >
        <HistoryIcon /> {t("global.jobs")}
      </Typography>
      <JobStepper jobs={jobs} jobsProgressById={jobsProgressById} />
    </Stack>
  );
}

export default LauncherHistory;
