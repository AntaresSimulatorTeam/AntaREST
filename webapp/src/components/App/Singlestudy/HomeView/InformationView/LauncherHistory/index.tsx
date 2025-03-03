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

import { Paper, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AxiosError } from "axios";
import HistoryIcon from "@mui/icons-material/History";
import moment from "moment";
import type { LaunchJob, LaunchJobsProgress, StudyMetadata } from "../../../../../../types/types";
import { getStudyJobs, mapLaunchJobDTO } from "../../../../../../services/api/study";
import { addWsEventListener, subscribeWsChannels } from "../../../../../../services/webSocket/ws";
import JobStepper from "./JobStepper";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { getJobProgress } from "../../../../../../services/api/launcher";
import type { WsEvent } from "@/services/webSocket/types";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";

interface Props {
  study: StudyMetadata | undefined;
}

function LauncherHistory(props: Props) {
  const { study } = props;
  const [t] = useTranslation();
  const [studyJobs, setStudyJobs] = useState<LaunchJob[]>([]);
  const [studyJobsProgress, setStudyJobsProgress] = useState<LaunchJobsProgress>({});
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const handleEvents = useCallback(
    (event: WsEvent): void => {
      if (study === undefined) {
        return;
      }
      if (event.type === WsEventType.StudyJobStarted) {
        const newJob = mapLaunchJobDTO(event.payload);
        if (newJob.studyId === study.id) {
          const existingJobs = studyJobs || [];
          setStudyJobs([newJob].concat(existingJobs));
        }
      } else if (
        event.type === WsEventType.StudyJobStatusUpdate ||
        event.type === WsEventType.StudyJobCompleted
      ) {
        const newJob = mapLaunchJobDTO(event.payload);
        if (newJob.studyId === study.id) {
          const existingJobs = studyJobs || [];
          if (!existingJobs.find((j) => j.id === newJob.id)) {
            setStudyJobs([newJob].concat(existingJobs));
          } else {
            setStudyJobs(
              existingJobs.map((j) => {
                if (j.id === newJob.id) {
                  return newJob;
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
          const data = await getStudyJobs(sid);

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
      <JobStepper jobs={studyJobs} jobsProgress={studyJobsProgress} />
    </Paper>
  );
}

export default LauncherHistory;
