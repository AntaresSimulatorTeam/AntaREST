import { Box, Paper, styled, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
import { AxiosError } from "axios";
import HistoryIcon from "@mui/icons-material/History";
import {
  LaunchJob,
  LaunchJobDTO,
  StudyMetadata,
  WSEvent,
  WSMessage,
} from "../../../../../common/types";
import {
  getStudyJobs,
  mapLaunchJobDTO,
} from "../../../../../services/api/study";
import {
  addListener,
  removeListener,
  subscribe,
  unsubscribe,
  WsChannel,
} from "../../../../../store/websockets";
import JobStepper from "./JobStepper";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";

const TitleHeader = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  height: "60px",
}));

interface OwnTypes {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

const mapState = () => ({});

const mapDispatch = {
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

function LauncherHistory(props: PropTypes) {
  const {
    study,
    addWsListener,
    removeWsListener,
    subscribeChannel,
    unsubscribeChannel,
  } = props;
  const [t] = useTranslation();
  const [studyJobs, setStudyJobs] = useState<Array<LaunchJob>>([]);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const handleEvents = useCallback(
    (msg: WSMessage): void => {
      if (study === undefined) return;
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
              })
            );
          }
        }
      } else if (msg.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
        // TODO
      } else if (msg.type === WSEvent.STUDY_EDITED) {
        // TODO
      }
    },
    [study, studyJobs]
  );

  useEffect(() => {
    if (study) {
      const fetchStudyJob = async (sid: string) => {
        try {
          const data = await getStudyJobs(sid);
          setStudyJobs(data.reverse());
        } catch (e) {
          enqueueErrorSnackbar(t("jobs:failedtoretrievejobs"), e as AxiosError);
        }
      };
      fetchStudyJob(study.id);
    }
  }, [study, t, enqueueErrorSnackbar]);

  useEffect(() => {
    addWsListener(handleEvents);
    return () => removeWsListener(handleEvents);
  }, [addWsListener, removeWsListener, handleEvents]);

  useEffect(() => {
    studyJobs.forEach((job) => {
      subscribeChannel(WsChannel.JOB_STATUS + job.id);
    });
    return () => {
      studyJobs.forEach((job) => {
        unsubscribeChannel(WsChannel.JOB_STATUS + job.id);
      });
    };
  }, [studyJobs, subscribeChannel, unsubscribeChannel]);

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
        <Typography color="text.secondary">{t("main:jobs")}</Typography>
      </TitleHeader>
      <JobStepper jobs={studyJobs} />
    </Paper>
  );
}

export default connector(LauncherHistory);
