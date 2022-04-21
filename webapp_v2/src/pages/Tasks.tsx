/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useMemo } from "react";
import { AxiosError } from "axios";
import { connect, ConnectedProps } from "react-redux";
import debug from "debug";
import { useTranslation } from "react-i18next";
import AssignmentIcon from "@mui/icons-material/Assignment";
import { useSnackbar } from "notistack";
import moment from "moment";
import {
  useTheme,
  Typography,
  Box,
  CircularProgress,
  Tooltip,
} from "@mui/material";
import { Link } from "react-router-dom";
import { debounce } from "lodash";
import BlockIcon from "@mui/icons-material/Block";
import InfoIcon from "@mui/icons-material/Info";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import DownloadIcon from "@mui/icons-material/Download";
import { grey } from "@mui/material/colors";
import RootPage from "../components/common/page/RootPage";
import SimpleLoader from "../components/common/loaders/SimpleLoader";
import DownloadLink from "../components/common/DownloadLink";
import LogModal from "../components/common/LogModal";
import {
  addListener,
  removeListener,
  subscribe,
  unsubscribe,
  WsChannel,
} from "../store/websockets";
import JobTableView from "../components/tasks/JobTableView";
import { convertUTCToLocalTime, useNotif } from "../services/utils/index";
import {
  downloadJobOutput,
  killStudy,
  getStudyJobs,
  getStudies,
} from "../services/api/study";
import {
  convertFileDownloadDTO,
  FileDownload,
  getDownloadUrl,
  FileDownloadDTO,
  getDownloadsList,
} from "../services/api/downloads";
import { initStudies } from "../store/study";
import {
  LaunchJob,
  TaskDTO,
  TaskEventPayload,
  WSEvent,
  WSMessage,
  TaskType,
  TaskStatus,
} from "../common/types";
import enqueueErrorSnackbar from "../components/common/ErrorSnackBar";
import BasicModal from "../components/common/BasicModal";
import { getAllMiscRunningTasks, getTask } from "../services/api/tasks";
import { AppState } from "../store/reducers";
import LogView from "../components/tasks/LogView";

const logError = debug("antares:studymanagement:error");

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = {
  loadStudies: initStudies,
  addWsListener: addListener,
  removeWsListener: removeListener,
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function JobsListing(props: PropTypes) {
  const {
    studies,
    loadStudies,
    addWsListener,
    removeWsListener,
    subscribeChannel,
    unsubscribeChannel,
  } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [jobs, setJobs] = useState<LaunchJob[]>([]);
  const [downloads, setDownloads] = useState<FileDownload[]>([]);
  const [tasks, setTasks] = useState<Array<TaskDTO>>([]);
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<
    string | undefined
  >();
  const [messageModalOpen, setMessageModalOpen] = useState<
    string | undefined
  >();

  const init = async () => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        const allStudies = await getStudies();
        loadStudies(allStudies);
      }
      const allJobs = await getStudyJobs(undefined, false);
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
        createNotif,
        t("jobs:failedtoretrievejobs"),
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

  const exportJobOutput = debounce(
    async (jobId: string): Promise<void> => {
      try {
        await downloadJobOutput(jobId);
      } catch (e) {
        enqueueErrorSnackbar(
          enqueueSnackbar,
          t("singlestudy:failedToExportOutput"),
          e as AxiosError
        );
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
        enqueueErrorSnackbar(
          enqueueSnackbar,
          t("singlestudy:failtokilltask"),
          e as AxiosError
        );
      }
      setOpenConfirmationModal(undefined);
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
    addWsListener(listener);
    return () => {
      removeWsListener(listener);
    };
  }, [addWsListener, removeWsListener, downloads, tasks, setTasks]);

  useEffect(() => {
    if (tasks) {
      tasks.forEach((task) => {
        subscribeChannel(WsChannel.TASK + task.id);
      });
      return () => {
        tasks.forEach((task) => {
          unsubscribeChannel(WsChannel.TASK + task.id);
        });
      };
    }
    return () => {
      /* noop */
    };
  }, [tasks, subscribeChannel, unsubscribeChannel]);

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
                  `${t("main:unknown")} (${job.id})`}
              </Typography>
            </Link>
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
              width="165px"
              display="flex"
              justifyContent="flex-start"
              alignItems="center"
            >
              <CalendarTodayIcon sx={{ fontSize: 16, marginRight: "0.5em" }} />
              {convertUTCToLocalTime(job.creationDate)}
            </Box>
            <Box
              width="165px"
              display="flex"
              justifyContent="flex-start"
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
                <Tooltip title={t("singlestudy:killStudy") as string}>
                  <BlockIcon
                    sx={{
                      mb: "4px",
                      cursor: "pointer",
                      color: "error.light",
                      "&:hover": { color: "error.dark" },
                    }}
                    onClick={() => setOpenConfirmationModal(job.id)}
                  />
                </Tooltip>
              ) : (
                <Box />
              )}
            </Box>
            <Box>
              {job.status === "success" ? (
                <Tooltip title={t("jobs:download") as string}>
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
            <LogView job={job} logButton logErrorButton />
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
            {`(${t("downloads:expirationDate")} : ${convertUTCToLocalTime(
              download.expirationDate
            )})`}
          </Box>
        ),
        action: download.failed ? (
          <Tooltip title={t("singlestudy:failedToExportOutput") as string}>
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
              <DownloadLink url={getDownloadUrl(download.id)}>
                <Tooltip title={t("jobs:download") as string}>
                  <DownloadIcon
                    sx={{
                      fontSize: 22,
                      color: "action.active",
                      cursor: "pointer",
                      "&:hover": { color: "action.hover" },
                    }}
                  />
                </Tooltip>
              </DownloadLink>
            ) : (
              <Tooltip title={t("jobs:loading") as string}>
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
              <Tooltip title={t("jobs:loading") as string}>
                <CircularProgress
                  color="primary"
                  style={{ width: "18px", height: "18px" }}
                />
              </Tooltip>
            )}
            {task.result && !task.result.success && (
              <Tooltip title={t("variants:taskFailed") as string}>
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

  return (
    <RootPage title={t("main:tasks")} titleIcon={AssignmentIcon}>
      <Box
        flexGrow={1}
        overflow="hidden"
        width="100%"
        display="flex"
        position="relative"
      >
        {!loaded && <SimpleLoader />}
        {loaded && <JobTableView content={content || []} />}
        {openConfirmationModal && (
          <BasicModal
            open={!!openConfirmationModal}
            title={t("main:confirmationModalTitle")}
            closeButtonLabel={t("main:noButton")}
            actionButtonLabel={t("main:yesButton")}
            onActionButtonClick={() => killTask(openConfirmationModal)}
            onClose={() => setOpenConfirmationModal(undefined)}
            rootStyle={{
              maxWidth: "800px",
              maxHeight: "800px",
              display: "flex",
              flexFlow: "column nowrap",
              alignItems: "center",
            }}
          >
            <Typography sx={{ p: 3 }}>
              {t("singlestudy:confirmKill")}
            </Typography>
          </BasicModal>
        )}
        <LogModal
          isOpen={!!messageModalOpen}
          title={t("singlestudy:taskLog")}
          content={messageModalOpen}
          close={() => setMessageModalOpen(undefined)}
          style={{ width: "600px", height: "300px" }}
        />
      </Box>
    </RootPage>
  );
}

export default connector(JobsListing);
