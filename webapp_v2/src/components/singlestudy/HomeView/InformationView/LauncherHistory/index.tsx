import { Paper } from "@mui/material";
import { useSnackbar } from "notistack";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
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
} from "../../../../../store/websockets";
import JobStepper from "./JobStepper";

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
  const { study, addWsListener, removeWsListener } = props;
  const [t] = useTranslation();
  const [studyJobs, setStudyJobs] = useState<Array<LaunchJob>>([]);
  const { enqueueSnackbar } = useSnackbar();

  const fetchStudyJob = async (sid: string) => {
    try {
      const data = await getStudyJobs(sid);
      setStudyJobs(data.reverse());
    } catch (e) {
      console.log("Failed to fetch study data", sid, e);
    }
  };

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
        // fetchStudyInfo();
      }
    },
    [study, studyJobs]
  );

  useEffect(() => {
    if (study) {
      fetchStudyJob(study.id);
    }
  }, [study, t, enqueueSnackbar]);

  useEffect(() => {
    addWsListener(handleEvents);
    return () => removeWsListener(handleEvents);
  }, [addWsListener, removeWsListener, handleEvents]);

  return (
    <Paper
      sx={{
        flex: 1,
        bgcolor: "rgba(36, 207, 157, 0.05)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
        mr: 1,
        p: 2,
      }}
    >
      <JobStepper jobs={studyJobs} />
    </Paper>
  );
}

export default connector(LauncherHistory);
