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

import ViewWrapper from "@/components/common/page/ViewWrapper";
import { resetTaskNotifications } from "@/redux/ducks/ui";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import AssignmentIcon from "@mui/icons-material/Assignment";
import BlockIcon from "@mui/icons-material/Block";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import DownloadIcon from "@mui/icons-material/Download";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import InfoIcon from "@mui/icons-material/Info";
import {
  Box,
  Chip,
  CircularProgress,
  Tooltip,
  Typography,
  Link as MuiLink,
  colors,
  useTheme,
} from "@mui/material";
import type { AxiosError } from "axios";
import debug from "debug";
import debounce from "lodash/debounce";
import moment from "moment";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useMount } from "react-use";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { fetchStudies } from "../../../redux/ducks/studies";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudies, getUsersById } from "../../../redux/selectors";
import {
  convertFileDownloadDTO,
  getDownloadUrl,
  getDownloadsList,
  type FileDownload,
} from "../../../services/api/downloads";
import { getJobProgress } from "../../../services/api/launcher";
import { downloadJobOutput, getStudyJobs, killStudy } from "../../../services/api/study";
import { getTask, getTasks } from "../../../services/api/tasks";
import { TaskStatus } from "../../../services/api/tasks/constants";
import type { TaskDTO } from "../../../services/api/tasks/types";
import { convertUTCToLocalTime } from "../../../services/utils/index";
import { addWsEventListener, subscribeWsChannels } from "../../../services/webSocket/ws";
import type { LaunchJob, LaunchJobsProgress, TaskView } from "../../../types/types";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import DownloadLink from "../../common/DownloadLink";
import LinearProgressWithLabel from "../../common/LinearProgressWithLabel";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import LogModal from "../../common/LogModal";
import RootPage from "../../common/page/RootPage";
import JobTableView from "./JobTableView";
import LaunchJobLogView from "./LaunchJobLogView";
import { TASK_TYPES_MANAGED } from "./utils";

const logError = debug("antares:studymanagement:error");

function JobsListing() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const theme = useTheme();
  const [jobs, setJobs] = useState<LaunchJob[]>([]);
  const [downloads, setDownloads] = useState<FileDownload[]>([]);
  const [tasks, setTasks] = useState<TaskDTO[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [openConfirmationDialog, setOpenConfirmationDialog] = useState<string | undefined>();
  const [messageModalOpen, setMessageModalOpen] = useState<string | undefined>();
  const studies = useAppSelector(getStudies);
  const usersByID = useAppSelector(getUsersById);
  const dispatch = useAppDispatch();
  const [studyJobsProgress, setStudyJobsProgress] = useState<LaunchJobsProgress>({});

  useMount(() => {
    dispatch(resetTaskNotifications());
  });

  const init = async (fetchOnlyLatest = true) => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        await dispatch(fetchStudies()).unwrap();
      }
      const allJobs = await getStudyJobs(undefined, true, fetchOnlyLatest);
      setJobs(allJobs);

      const dlList = await getDownloadsList();
      setDownloads(dlList);

      const allTasks = await getTasks({
        status: [TaskStatus.Running, TaskStatus.Pending, TaskStatus.Failed, TaskStatus.Completed],
        type: TASK_TYPES_MANAGED,
      });

      const dateThreshold = moment().subtract(1, "m");
      setTasks(
        allTasks.filter(
          (task) =>
            !task.completion_date_utc ||
            moment.utc(task.completion_date_utc).isAfter(dateThreshold),
        ),
      );

      const initJobProgress: Record<string, number> = {};
      const jobProgress = await Promise.all(
        allJobs
          .filter((o) => o.status === "running")
          .map(async (item) => ({
            id: item.id,
            progress: await getJobProgress({ id: item.id }),
          })),
      );

      setStudyJobsProgress(
        jobProgress.reduce((agg, cur) => ({ ...agg, [cur.id]: cur.progress }), initJobProgress),
      );
    } catch (e) {
      logError("woops", e);
      enqueueErrorSnackbar(t("global.error.failedtoretrievejobs"), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const renderStatus = (job: LaunchJob) => {
    let color = theme.palette.grey[400];
    if (job.status === "success") {
      color = theme.palette.success.main;
    } else if (job.status === "failed") {
      color = theme.palette.error.main;
    } else if (job.status === "running") {
      color = theme.palette.warning.main;
    }
    return <FiberManualRecordIcon style={{ color, fontSize: "10px", marginRight: "8px" }} />;
  };

  const renderTags = (job: LaunchJob) => {
    return (
      <Box sx={{ ml: 2 }}>
        {job.launcherParams?.xpansion && (
          <Chip label="Xpansion" sx={{ m: 0.25, color: "white", bgcolor: colors.indigo[300] }} />
        )}
        {job.launcherParams?.adequacy_patch && (
          <Chip
            label="Adequacy patch"
            sx={{ m: 0.25, color: "white", bgcolor: colors.indigo[300] }}
          />
        )}
      </Box>
    );
  };

  const exportJobOutput = debounce(
    async (jobId: string): Promise<void> => {
      try {
        await downloadJobOutput(jobId);
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.exportOutput"), e as AxiosError);
      }
    },
    2000,
    { leading: true },
  );

  const killTask = (jobId: string) => {
    (async () => {
      try {
        await killStudy(jobId);
      } catch (e) {
        enqueueErrorSnackbar(t("study.failtokilltask"), e as AxiosError);
      }
      setOpenConfirmationDialog(undefined);
    })();
  };
  useEffect(() => {
    const listener = async (ev: WsEvent) => {
      if (ev.type === WsEventType.TaskCompleted || ev.type === WsEventType.TaskFailed) {
        const taskId = ev.payload.id;
        if (tasks?.find((task) => task.id === taskId)) {
          try {
            const updatedTask = await getTask({ id: taskId });
            setTasks(tasks.filter((task) => task.id !== updatedTask.id).concat([updatedTask]));
          } catch (error) {
            logError(error);
          }
        }
      } else if (ev.type === WsEventType.DownloadCreated) {
        setDownloads((downloads || []).concat([convertFileDownloadDTO(ev.payload)]));
      } else if (ev.type === WsEventType.DownloadReady || ev.type === WsEventType.DownloadFailed) {
        setDownloads(
          (downloads || []).map((d) => {
            const fileDownload = ev.payload;
            if (d.id === fileDownload.id) {
              return convertFileDownloadDTO(fileDownload);
            }
            return d;
          }),
        );
      } else if (ev.type === WsEventType.DownloadExpired) {
        setDownloads(
          (downloads || []).filter((d) => {
            const fileDownload = ev.payload;
            return d.id !== fileDownload.id;
          }),
        );
      } else if (ev.type === WsEventType.LaunchProgress) {
        const message = ev.payload;
        setStudyJobsProgress((studyJobsProgress) => ({
          ...studyJobsProgress,
          [message.id]: message.progress,
        }));
      }
    };

    return addWsEventListener(listener);
  }, [downloads, tasks, setTasks]);

  useEffect(() => {
    if (tasks) {
      const channels = tasks.map((task) => WsChannel.Task + task.id);
      return subscribeWsChannels(channels);
    }
  }, [tasks]);

  useEffect(() => {
    const channels = jobs.map((job) => WsChannel.JobStatus + job.id);
    return subscribeWsChannels(channels);
  }, [jobs]);

  useEffect(() => {
    init();
  }, []);

  const jobsMemo = useMemo<TaskView[]>(
    () =>
      jobs.map((job) => ({
        id: job.id,
        name: (
          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
            <Box flexGrow={0.6} display="flex" alignItems="center" width="60%">
              {renderStatus(job)}
              <MuiLink
                color="inherit"
                underline="hover"
                component={Link}
                to={`/studies/${encodeURI(job.studyId)}`}
              >
                {studies.find((s) => s.id === job.studyId)?.name ||
                  `${t("global.unknown")} (${job.id})`}
              </MuiLink>
              {renderTags(job)}
            </Box>
            {job.status === "running" && (
              <LinearProgressWithLabel
                value={studyJobsProgress[job.id] as number}
                tooltip="Progression"
                sx={{ width: "20%" }}
              />
            )}
          </Box>
        ),
        dateView: (
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "center",
              flexDirection: "column",
              fontSize: "0.85rem",
            }}
          >
            <Box width="168px" display="flex" justifyContent="space-between" alignItems="center">
              <CalendarTodayIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
              {convertUTCToLocalTime(job.creationDate)}
            </Box>
            <Box width="168px" display="flex" justifyContent="space-between" alignItems="center">
              {job.completionDate && (
                <>
                  <EventAvailableIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
                  {convertUTCToLocalTime(job.completionDate)}
                </>
              )}
            </Box>
          </Box>
        ),
        action: (
          <Box display="flex" alignItems="center" justifyContent="flex-end">
            <Box display="flex" alignItems="center" justifyContent="flex-end">
              {job.status === "running" ? (
                <Tooltip title={t("study.killStudy") as string}>
                  <BlockIcon
                    sx={{
                      mb: "4px",
                      cursor: "pointer",
                      color: "error.light",
                      "&:hover": { color: "error.dark" },
                    }}
                    onClick={() => setOpenConfirmationDialog(job.id)}
                  />
                </Tooltip>
              ) : (
                <Box />
              )}
            </Box>
            <Box>
              {job.status === "success" ? (
                <Tooltip title={t("global.download") as string}>
                  <DownloadIcon
                    sx={{
                      fontSize: 22,
                      color: "action.active",
                      cursor: "pointer",
                    }}
                    onClick={() => exportJobOutput(job.id)}
                  />
                </Tooltip>
              ) : (
                <Box />
              )}
            </Box>
            <LaunchJobLogView job={job} logButton logErrorButton />
          </Box>
        ),
        date: job.completionDate || job.creationDate,
        type: "LAUNCH",
        status: job.status === "running" ? "running" : "",
        userName: (job.ownerId && usersByID[job.ownerId]?.name) || "",
      })),
    [jobs, studyJobsProgress],
  );

  const downloadsMemo = useMemo<TaskView[]>(
    () =>
      downloads.map((download) => ({
        id: download.id,
        name: download.name,
        dateView: (
          <Box sx={{ fontSize: "0.85rem" }}>
            {`(${t("downloads.expirationDate")} : ${convertUTCToLocalTime(
              download.expirationDate,
            )})`}
          </Box>
        ),
        action: download.failed ? (
          <Tooltip title={t("study.error.exportOutput") as string}>
            <InfoIcon
              sx={{
                width: "18px",
                height: "auto",
                cursor: "pointer",
                color: "error.light",
                "&:hover": {
                  color: "error.dark",
                },
              }}
              onClick={() => setMessageModalOpen(download.errorMessage)}
            />
          </Tooltip>
        ) : (
          <Box>
            {download.ready ? (
              <DownloadLink
                title={t("global.download") as string}
                url={getDownloadUrl(download.id)}
              >
                <DownloadIcon
                  sx={{
                    fontSize: 22,
                  }}
                />
              </DownloadLink>
            ) : (
              <Tooltip title={t("global.loading") as string}>
                <CircularProgress color="primary" style={{ width: "18px", height: "18px" }} />
              </Tooltip>
            )}
          </Box>
        ),
        date: moment(download.expirationDate).subtract(1, "days").format("YYYY-MM-DD HH:mm:ss"),
        type: "DOWNLOAD",
        status: !download.ready && !download.failed ? "running" : "",
      })),
    [downloads],
  );

  const tasksMemo = useMemo<TaskView[]>(
    () =>
      tasks.map((task) => ({
        id: task.id,
        name: task.name,
        dateView: (
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "center",
              flexDirection: "column",
              color: colors.grey[500],
              fontSize: "0.85rem",
            }}
          >
            <Box width="165px" display="flex" justifyContent="flex-start" alignItems="center">
              <CalendarTodayIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
              {convertUTCToLocalTime(task.creation_date_utc)}
            </Box>
            <Box width="165px" display="flex" justifyContent="flex-start" alignItems="center">
              {task.completion_date_utc && (
                <>
                  <EventAvailableIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
                  {convertUTCToLocalTime(task.completion_date_utc)}
                </>
              )}
            </Box>
          </Box>
        ),
        action: (
          <Box>
            {!task.completion_date_utc && (
              <Tooltip title={t("global.loading") as string}>
                <CircularProgress color="primary" style={{ width: "18px", height: "18px" }} />
              </Tooltip>
            )}
            {task.result && !task.result.success && (
              <Tooltip title={t("variants.error.taskFailed") as string}>
                <InfoIcon
                  sx={{
                    width: "18px",
                    height: "auto",
                    cursor: "pointer",
                    color: "error.light",
                    "&:hover": {
                      color: "error.dark",
                    },
                  }}
                  onClick={() => setMessageModalOpen(`${task.result?.message}`)}
                />
              </Tooltip>
            )}
          </Box>
        ),
        date: task.completion_date_utc || task.creation_date_utc,
        type: task.type || "UNKNOWN",
        status: task.status === TaskStatus.Running ? "running" : "",
        userName: (task.owner && usersByID[task.owner]?.name) || "",
      })),
    [tasks],
  );

  const content = [...jobsMemo, ...downloadsMemo, ...tasksMemo];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage title={t("tasks.title")} titleIcon={AssignmentIcon}>
      <ViewWrapper flex={{ gap: 1 }}>
        {loaded ? (
          <JobTableView content={content || []} refresh={() => init(false)} />
        ) : (
          <SimpleLoader />
        )}
        {openConfirmationDialog && (
          <ConfirmationDialog
            title={t("dialog.title.confirmation")}
            onCancel={() => setOpenConfirmationDialog(undefined)}
            onConfirm={() => killTask(openConfirmationDialog)}
            alert="warning"
            open={!!openConfirmationDialog}
          >
            <Typography sx={{ p: 3 }}>{t("study.question.killJob")}</Typography>
          </ConfirmationDialog>
        )}
        <LogModal
          isOpen={!!messageModalOpen}
          content={messageModalOpen}
          close={() => setMessageModalOpen(undefined)}
        />
      </ViewWrapper>
    </RootPage>
  );
}

export default JobsListing;
