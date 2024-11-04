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

import { Box, Paper, styled, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import HistoryIcon from "@mui/icons-material/History";
import moment from "moment";
import {
  LaunchJob,
  LaunchJobDTO,
  LaunchJobProgressDTO,
  LaunchJobsProgress,
  StudyMetadata,
  WSEvent,
  WSMessage,
} from "@/common/types";
import { getStudyJobs, mapLaunchJobDTO } from "@/services/api/study";
import {
  addWsMessageListener,
  sendWsSubscribeMessage,
  WsChannel,
} from "@/services/webSockets";
import JobStepper from "./JobStepper";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { getProgress } from "@/services/api/tasks";

const TitleHeader = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  height: "60px",
}));

interface Props {
  study: StudyMetadata | undefined;
}

function LauncherHistory(props: Props) {
  const { study } = props;
  const [t] = useTranslation();
  const [studyJobs, setStudyJobs] = useState<LaunchJob[]>([]);
  const [studyJobsProgress, setStudyJobsProgress] =
    useState<LaunchJobsProgress>({});
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const handleEvents = useCallback(
    (msg: WSMessage): void => {
      if (study === undefined) {
        return;
      }
      if (msg.type === WSEvent.STUDY_JOB_STARTED) {
        const newJob = mapLaunchJobDTO(msg.payload as LaunchJobDTO);
        if (newJob.studyId === study.id) {
          const existingJobs = studyJobs || [];
          setStudyJobs([newJob].concat(existingJobs));
        }
      } else if (
        msg.type === WSEvent.STUDY_JOB_STATUS_UPDATE ||
        msg.type === WSEvent.STUDY_JOB_COMPLETED
      ) {
        const newJob = mapLaunchJobDTO(msg.payload as LaunchJobDTO);
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
      } else if (msg.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
        // TODO
      } else if (msg.type === WSEvent.STUDY_EDITED) {
        // TODO
      } else if (msg.type === WSEvent.LAUNCH_PROGRESS) {
        const message = msg.payload as LaunchJobProgressDTO;
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
                progress: await getProgress(item.id),
              })),
          );

          setStudyJobsProgress(
            jobProgress.reduce(
              (agg, cur) => ({ ...agg, [cur.id]: cur.progress }),
              initJobProgress,
            ),
          );

          setStudyJobs(
            data.sort((j1, j2) => {
              const defaultCompletionDate = moment();
              const j1CompletionDate =
                j1.completionDate || defaultCompletionDate;
              const j2CompletionDate =
                j2.completionDate || defaultCompletionDate;
              if (j1CompletionDate === j2CompletionDate) {
                return moment(j1.creationDate).isAfter(moment(j2.creationDate))
                  ? -1
                  : 1;
              }
              return moment(j1CompletionDate).isAfter(moment(j2CompletionDate))
                ? -1
                : 1;
            }),
          );
        } catch (e) {
          enqueueErrorSnackbar(
            t("global.error.failedtoretrievejobs"),
            e as AxiosError,
          );
        }
      };
      fetchStudyJob(study.id);
    }
  }, [study, t, enqueueErrorSnackbar]);

  useEffect(() => {
    return addWsMessageListener(handleEvents);
  }, [handleEvents]);

  useEffect(() => {
    const channels = studyJobs.map((job) => WsChannel.JobStatus + job.id);
    return sendWsSubscribeMessage(channels);
  }, [studyJobs]);

  return (
    <Paper
      sx={{
        width: 0,
        flex: 1,
        bgcolor: "rgba(36, 207, 157, 0.05)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
        mr: 1,
        px: 2,
      }}
    >
      <TitleHeader>
        <HistoryIcon sx={{ color: "text.secondary", mr: 1 }} />
        <Typography color="text.secondary">{t("global.jobs")}</Typography>
      </TitleHeader>
      <JobStepper jobs={studyJobs} jobsProgress={studyJobsProgress} />
    </Paper>
  );
}

export default LauncherHistory;
