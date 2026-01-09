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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { getJobProgress } from "@/services/api/launcher";
import { getJobs } from "@/services/api/launcher/jobs";
import { adaptJobDtoToJob } from "@/services/api/launcher/jobs/adapters";
import type { Job } from "@/services/api/launcher/jobs/types";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { addWsEventListener, subscribeWsChannels } from "@/services/webSocket/ws";
import type { LaunchJobsProgress, StudyMetadata } from "@/types/types";
import HistoryIcon from "@mui/icons-material/History";
import { Paper, Typography } from "@mui/material";
import type { AxiosError } from "axios";
import moment from "moment";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import JobStepper from "./JobStepper";

interface Props {
  study: StudyMetadata | undefined;
}

function LauncherHistory(props: Props) {
  const { study } = props;
  const [t] = useTranslation();
  const [studyJobs, setStudyJobs] = useState<Job[]>([]);
  const [studyJobsProgress, setStudyJobsProgress] = useState<LaunchJobsProgress>({});
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const handleEvents = useCallback(
    (event: WsEvent): void => {
      if (study === undefined) {
        return;
      }
      if (event.type === WsEventType.StudyJobStarted) {
        const job = adaptJobDtoToJob(event.payload);
        if (job.studyId === study.id) {
          const existingJobs = studyJobs || [];
          setStudyJobs([job].concat(existingJobs));
        }
      } else if (
        event.type === WsEventType.StudyJobStatusUpdate ||
        event.type === WsEventType.StudyJobCompleted
      ) {
        const job = adaptJobDtoToJob(event.payload);
        if (job.studyId === study.id) {
          const existingJobs = studyJobs || [];
          if (!existingJobs.find((j) => j.id === job.id)) {
            setStudyJobs([job].concat(existingJobs));
          } else {
            setStudyJobs(
              existingJobs.map((j) => {
                if (j.id === job.id) {
                  return job;
                }
                return j;
              }),
            );
          }
        }
      } else if (event.type === WsEventType.StudyJobLogUpdate) {
        // TODO
      } else if (event.type === WsEventType.StudyEdited) {
        // TODO
      } else if (event.type === WsEventType.LaunchProgress) {
        const message = event.payload;
        setStudyJobsProgress((studyJobsProgress) => ({
          ...studyJobsProgress,
          [message.id]: message.progress,
        }));
      }
    },
    [study, studyJobs],
  );

  useEffect(() => {
    if (study) {
      const fetchStudyJob = async (sid: string) => {
        try {
          const data = await getJobs({ studyId: sid });

          const initJobProgress: Record<string, number> = {};
          const jobProgress = await Promise.all(
            data
              .filter((o) => o.status === "running")
              .map(async (item) => ({
                id: item.id,
                progress: await getJobProgress({ id: item.id }),
              })),
          );

          setStudyJobsProgress(
            jobProgress.reduce((agg, cur) => ({ ...agg, [cur.id]: cur.progress }), initJobProgress),
          );

          setStudyJobs(
            data.sort((j1, j2) => {
              const defaultCompletionDate = moment();
              const j1CompletionDate = j1.completionDate || defaultCompletionDate;
              const j2CompletionDate = j2.completionDate || defaultCompletionDate;
              if (j1CompletionDate === j2CompletionDate) {
                return moment(j1.creationDate).isAfter(moment(j2.creationDate)) ? -1 : 1;
              }
              return moment(j1CompletionDate).isAfter(moment(j2CompletionDate)) ? -1 : 1;
            }),
          );
        } catch (e) {
          enqueueErrorSnackbar(t("global.error.failedtoretrievejobs"), e as AxiosError);
        }
      };
      fetchStudyJob(study.id);
    }
  }, [study, t, enqueueErrorSnackbar]);

  useEffect(() => {
    return addWsEventListener(handleEvents);
  }, [handleEvents]);

  useEffect(() => {
    const channels = studyJobs.map((job) => WsChannel.JobStatus + job.id);
    return subscribeWsChannels(channels);
  }, [studyJobs]);

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1,
        p: 2,
        flex: 1,
      }}
      elevation={2}
    >
      <Typography color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <HistoryIcon /> {t("global.jobs")}
      </Typography>
      {study && <JobStepper studyId={study.id} jobs={studyJobs} jobsProgress={studyJobsProgress} />}
    </Paper>
  );
}

export default LauncherHistory;
