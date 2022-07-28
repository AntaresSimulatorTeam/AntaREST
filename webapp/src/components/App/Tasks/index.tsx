/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useMemo } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useTranslation } from "react-i18next";
import AssignmentIcon from "@mui/icons-material/Assignment";
import moment from "moment";
import {
  useTheme,
  Typography,
  Box,
  CircularProgress,
  Tooltip,
  Chip,
} from "@mui/material";
import { Link } from "react-router-dom";
import { debounce } from "lodash";
import BlockIcon from "@mui/icons-material/Block";
import InfoIcon from "@mui/icons-material/Info";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import DownloadIcon from "@mui/icons-material/Download";
import { grey, indigo } from "@mui/material/colors";
import RootPage from "../../common/page/RootPage";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import DownloadLink from "../../common/DownloadLink";
import LogModal from "../../common/LogModal";
import {
  addWsMessageListener,
  sendWsSubscribeMessage,
  WsChannel,
} from "../../../services/webSockets";
import JobTableView from "./JobTableView";
import { convertUTCToLocalTime } from "../../../services/utils/index";
import {
  downloadJobOutput,
  killStudy,
  getStudyJobs,
} from "../../../services/api/study";
import {
  convertFileDownloadDTO,
  FileDownload,
  getDownloadUrl,
  FileDownloadDTO,
  getDownloadsList,
} from "../../../services/api/downloads";
import { fetchStudies } from "../../../redux/ducks/studies";
import {
  LaunchJob,
  TaskDTO,
  TaskEventPayload,
  WSEvent,
  WSMessage,
  TaskType,
  TaskStatus,
} from "../../../common/types";
import { getAllMiscRunningTasks, getTask } from "../../../services/api/tasks";
import LaunchJobLogView from "./LaunchJobLogView";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { getStudies } from "../../../redux/selectors";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { resetTitle } from "../../../utils/textUtils";

const logError = debug("antares:studymanagement:error");

function JobsListing() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const theme = useTheme();
  const [jobs, setJobs] = useState<LaunchJob[]>([]);
  const [downloads, setDownloads] = useState<FileDownload[]>([]);
  const [tasks, setTasks] = useState<Array<TaskDTO>>([]);
  const [loaded, setLoaded] = useState(false);
  const [openConfirmationDialog, setOpenConfirmationDialog] = useState<
    string | undefined
  >();
  const [messageModalOpen, setMessageModalOpen] = useState<
    string | undefined
  >();
  const studies = useAppSelector(getStudies);
  const dispatch = useAppDispatch();

  const init = async (fetchOnlyLatest = true) => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        await dispatch(fetchStudies()).unwrap();
      }
      const allJobs = await getStudyJobs(undefined, false, fetchOnlyLatest);
      setJobs(allJobs);
      const dlList = await getDownloadsList();
      setDownloads(dlList);
      const allTasks = await getAllMiscRunningTasks();
      const dateThreshold = moment().subtract(1, "m");
      setTasks(
        allTasks.filter(
          (task) =>
            !task.completion_date_utc ||
            moment.utc(task.completion_date_utc).isAfter(dateThreshold)
        )
      );
    } catch (e) {
      logError("woops", e);
      enqueueErrorSnackbar(
        t("global.error.failedtoretrievejobs"),
        e as AxiosError
      );
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
    return (
      <FiberManualRecordIcon
        style={{ color, fontSize: "10px", marginRight: "8px" }}
      />
    );
  };

  const renderTags = (job: LaunchJob) => {
    return (
      <Box sx={{ ml: 2 }}>
        {job.launcherParams?.xpansion && (
          <Chip
            key="xpansion"
            label="Xpansion"
            variant="filled"
            sx={{ m: 0.25, color: "black", bgcolor: indigo[300] }}
          />
        )}
        {job.launcherParams?.adequacy_patch && (
          <Chip
            key="adequacy_patch"
            label="Adequacy patch"
            variant="filled"
            sx={{ m: 0.25, color: "black", bgcolor: indigo[300] }}
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
    { leading: true }
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
    const listener = async (ev: WSMessage) => {
      if (
        ev.type === WSEvent.TASK_COMPLETED ||
        ev.type === WSEvent.TASK_FAILED
      ) {
        const taskId = (ev.payload as TaskEventPayload).id;
        if (tasks?.find((task) => task.id === taskId)) {
          try {
            const updatedTask = await getTask(taskId);
            setTasks(
              tasks
                .filter((task) => task.id !== updatedTask.id)
                .concat([updatedTask])
            );
          } catch (error) {
            logError(error);
          }
        }
      } else if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        setDownloads(
          (downloads || []).concat([
            convertFileDownloadDTO(ev.payload as FileDownloadDTO),
          ])
        );
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        setDownloads(
          (downloads || []).map((d) => {
            const fileDownload = ev.payload as FileDownloadDTO;
            if (d.id === fileDownload.id) {
              return convertFileDownloadDTO(fileDownload);
            }
            return d;
          })
        );
      } else if (
        ev.type === WSEvent.DOWNLOAD_READY ||
        ev.type === WSEvent.DOWNLOAD_FAILED
      ) {
        setDownloads(
          (downloads || []).map((d) => {
            const fileDownload = ev.payload as FileDownloadDTO;
            if (d.id === fileDownload.id) {
              return convertFileDownloadDTO(fileDownload);
            }
            return d;
          })
        );
      } else if (ev.type === WSEvent.DOWNLOAD_EXPIRED) {
        setDownloads(
          (downloads || []).filter((d) => {
            const fileDownload = ev.payload as FileDownloadDTO;
            return d.id !== fileDownload.id;
          })
        );
      }
    };

    return addWsMessageListener(listener);
  }, [downloads, tasks, setTasks]);

  useEffect(() => {
    if (tasks) {
      const channels = tasks.map((task) => WsChannel.Task + task.id);
      return sendWsSubscribeMessage(channels);
    }
  }, [tasks]);

  useEffect(() => {
    init();
  }, []);

  const jobsMemo = useMemo(
    () =>
      jobs.map((job) => ({
        id: job.id,
        name: (
          <Box flexGrow={0.6} display="flex" alignItems="center" width="60%">
            {renderStatus(job)}
            <Link
              style={{ textDecoration: "none" }}
              to={`/studies/${encodeURI(job.studyId)}`}
            >
              <Typography sx={{ color: "white", fontSize: "0.95rem" }}>
                {studies.find((s) => s.id === job.studyId)?.name ||
                  `${t("global.unknown")} (${job.id})`}
              </Typography>
            </Link>
            {renderTags(job)}
          </Box>
        ),
        dateView: (
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "center",
              flexDirection: "column",
              color: grey[500],
              fontSize: "0.85rem",
            }}
          >
            <Box
              width="168px"
              display="flex"
              justifyContent="space-between"
              alignItems="center"
            >
              <CalendarTodayIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
              {convertUTCToLocalTime(job.creationDate)}
            </Box>
            <Box
              width="168px"
              display="flex"
              justifyContent="space-between"
              alignItems="center"
            >
              {job.completionDate && (
                <>
                  <EventAvailableIcon
                    sx={{ fontSize: 16, marginRight: "0.5em" }}
                  />
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
                      "&:hover": { color: "action.hover" },
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
        type: TaskType.LAUNCH,
        status: job.status === "running" ? "running" : "",
      })),
    [jobs]
  );

  const downloadsMemo = useMemo(
    () =>
      downloads.map((download) => ({
        id: download.id,
        name: (
          <Box sx={{ color: "white", fontSize: "0.95rem" }}>
            {download.name}
          </Box>
        ),
        dateView: (
          <Box sx={{ color: grey[500], fontSize: "0.85rem" }}>
            {`(${t("downloads.expirationDate")} : ${convertUTCToLocalTime(
              download.expirationDate
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
                    color: "action.active",
                    cursor: "pointer",
                    "&:hover": { color: "action.hover" },
                  }}
                />
              </DownloadLink>
            ) : (
              <Tooltip title={t("global.loading") as string}>
                <CircularProgress
                  color="primary"
                  style={{ width: "18px", height: "18px" }}
                />
              </Tooltip>
            )}
          </Box>
        ),
        date: moment(download.expirationDate)
          .subtract(1, "days")
          .format("YYYY-MM-DD HH:mm:ss"),
        type: TaskType.DOWNLOAD,
        status: !download.ready && !download.failed ? "running" : "",
      })),
    [downloads]
  );

  const tasksMemo = useMemo(
    () =>
      tasks.map((task) => ({
        id: task.id,
        name: (
          <Typography sx={{ color: "white", fontSize: "0.95rem" }}>
            {task.name}
          </Typography>
        ),
        dateView: (
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "center",
              flexDirection: "column",
              color: grey[500],
              fontSize: "0.85rem",
            }}
          >
            <Box
              width="165px"
              display="flex"
              justifyContent="flex-start"
              alignItems="center"
            >
              <CalendarTodayIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
              {convertUTCToLocalTime(task.creation_date_utc)}
            </Box>
            <Box
              width="165px"
              display="flex"
              justifyContent="flex-start"
              alignItems="center"
            >
              {task.completion_date_utc && (
                <>
                  <EventAvailableIcon
                    sx={{ fontSize: 16, marginRight: "0.5em" }}
                  />
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
                <CircularProgress
                  color="primary"
                  style={{ width: "18px", height: "18px" }}
                />
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
        type: task.type || TaskType.UNKNOWN,
        status: task.status === TaskStatus.RUNNING ? "running" : "",
      })),
    [tasks]
  );

  const content = jobsMemo.concat(downloadsMemo.concat(tasksMemo));

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  resetTitle();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RootPage title={t("tasks.title")} titleIcon={AssignmentIcon}>
      <Box
        flexGrow={1}
        overflow="hidden"
        width="100%"
        display="flex"
        position="relative"
      >
        {!loaded && <SimpleLoader />}
        {loaded && (
          <JobTableView content={content || []} refresh={() => init(false)} />
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
      </Box>
    </RootPage>
  );
}

export default JobsListing;
