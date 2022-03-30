/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect, useMemo } from 'react';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import debug from 'debug';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import moment from 'moment';
import { makeStyles, createStyles, Theme, useTheme, Typography, Box, CircularProgress } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import BlockIcon from '@material-ui/icons/Block';
import InfoIcon from '@material-ui/icons/Info';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import DownloadLink from '../ui/DownloadLink';
import LogModal from '../ui/LogModal';
import { addListener, removeListener, subscribe, unsubscribe, WsChannel } from '../../ducks/websockets';
import JobTableView from './JobTableView';
import { convertUTCToLocalTime, useNotif } from '../../services/utils';
import { AppState } from '../../App/reducers';
import { downloadJobOutput, killStudy, getStudyJobs, getStudies } from '../../services/api/study';
import { convertFileDownloadDTO, FileDownload, getDownloadUrl, FileDownloadDTO, getDownloadsList } from '../../services/api/downloads';
import { initStudies } from '../../ducks/study';
import { LaunchJob, TaskDTO, TaskEventPayload, WSEvent, WSMessage } from '../../common/types';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import ConfirmationModal from '../ui/ConfirmationModal';
import { getAllMiscRunningTasks, getTask } from '../../services/api/tasks';
import { TaskType } from './types';
import LogView from './LogView';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'hidden',
    width: '100%',
    display: 'flex',
  },
  titleblock: {
    flexGrow: 0.6,
    display: 'flex',
    alignItems: 'center',
    width: '60%',
  },
  title: {
    color: theme.palette.primary.main,
    fontSize: '0.95rem',
  },
  dateblock: {
    color: theme.palette.grey[500],
    fontSize: '0.85em',
  },
  dateicon: {
    marginRight: '0.5em',
  },
  dot: {
    width: '0.5em',
    height: '0.5em',
    borderRadius: '50%',
    marginRight: theme.spacing(1),
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  actionButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  blockIcon: {
    cursor: 'pointer',
    color: theme.palette.error.light,
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
  downloadIcon: {
    cursor: 'pointer',
    margin: theme.spacing(0.5),
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  errorIcon: {
    width: '18px',
    height: 'auto',
    cursor: 'pointer',
    color: theme.palette.error.main,
    '&:hover': {
      color: theme.palette.error.dark,
    },
  },
}));

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
  loadStudies: initStudies,
  addWsListener: addListener,
  removeWsListener: removeListener,
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const JobsListing = (props: PropTypes) => {
  const { studies, loadStudies, addWsListener, removeWsListener, subscribeChannel, unsubscribeChannel } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [jobs, setJobs] = useState<LaunchJob[]>([]);
  const [downloads, setDownloads] = useState<FileDownload[]>([]);
  const [tasks, setTasks] = useState<Array<TaskDTO>>([]);
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<string | undefined>();
  const [messageModalOpen, setMessageModalOpen] = useState<string | undefined>();

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
      const dateThreshold = moment().subtract(1, 'm');
      setTasks(allTasks.filter((task) => !task.completion_date_utc || moment.utc(task.completion_date_utc).isAfter(dateThreshold)));
    } catch (e) {
      logError('woops', e);
      enqueueErrorSnackbar(createNotif, 'ça marche pas', e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const renderStatus = (job: LaunchJob) => {
    let color = theme.palette.grey[400];
    if (job.status === 'success') {
      color = theme.palette.success.main;
    } else if (job.status === 'failed') {
      color = theme.palette.error.main;
    } else if (job.status === 'running') {
      color = theme.palette.warning.main;
    }
    return (<Box className={classes.dot} style={{ backgroundColor: color }} />);
  };

  const exportJobOutput = async (jobId: string): Promise<void> => {
    try {
      await downloadJobOutput(jobId);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failedToExportOutput'), e as AxiosError);
    }
  };

  const killTask = (jobId: string) => {
    (async () => {
      try {
        await killStudy(jobId);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failtokilltask'), e as AxiosError);
      }
      setOpenConfirmationModal(undefined);
    })();
  };

  useEffect(() => {
    const listener = async (ev: WSMessage) => {
      if (ev.type === WSEvent.TASK_COMPLETED || ev.type === WSEvent.TASK_FAILED) {
        const taskId = (ev.payload as TaskEventPayload).id;
        if (tasks?.find((task) => task.id === taskId)) {
          try {
            const updatedTask = await getTask(taskId);
            setTasks(tasks.filter((task) => task.id !== updatedTask.id).concat([updatedTask]));
          } catch (error) {
            logError(error);
          }
        }
      } else if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        setDownloads((downloads || []).concat([convertFileDownloadDTO(ev.payload as FileDownloadDTO)]));
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        setDownloads((downloads || []).map((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          if (d.id === fileDownload.id) {
            return convertFileDownloadDTO(fileDownload);
          }
          return d;
        }));
      } else if (ev.type === WSEvent.DOWNLOAD_READY || ev.type === WSEvent.DOWNLOAD_FAILED) {
        setDownloads((downloads || []).map((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          if (d.id === fileDownload.id) {
            return convertFileDownloadDTO(fileDownload);
          }
          return d;
        }));
      } else if (ev.type === WSEvent.DOWNLOAD_EXPIRED) {
        setDownloads((downloads || []).filter((d) => {
          const fileDownload = (ev.payload as FileDownloadDTO);
          return d.id !== fileDownload.id;
        }));
      }
    };
    addWsListener(listener);
    return () => { removeWsListener(listener); };
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
    return () => { /* noop */ };
  }, [tasks, subscribeChannel, unsubscribeChannel]);

  useEffect(() => {
    init();
  }, []);

  const jobsMemo = useMemo(() => jobs.map((job) => ({
    name: (
      <Box className={classes.titleblock}>
        {renderStatus(job)}
        <Link to={`/study/${encodeURI(job.studyId)}`}>
          <Typography className={classes.title}>
            {studies.find((s) => s.id === job.studyId)?.name}
          </Typography>
        </Link>
      </Box>
    ),
    dateView: (
      <Box className={classes.dateblock}>
        <Box>
          <FontAwesomeIcon className={classes.dateicon} icon="calendar" />
          {convertUTCToLocalTime(job.creationDate)}
        </Box>
        <Box>
          {job.completionDate && (
            <>
              <FontAwesomeIcon className={classes.dateicon} icon="calendar-check" />
              {convertUTCToLocalTime(job.completionDate)}
            </>
          )}
        </Box>
      </Box>
    ),
    action: (
      <Box className={classes.actions}>
        <Box className={classes.actionButton}>
          {job.status === 'running' ? <BlockIcon className={classes.blockIcon} onClick={() => setOpenConfirmationModal(job.id)} /> : <Box />}
        </Box>
        <Box>
          {job.status === 'success' ? <FontAwesomeIcon size="lg" className={classes.downloadIcon} icon="download" onClick={() => exportJobOutput(job.id)} /> : <Box />}
        </Box>
        <LogView job={job} logButton logErrorButton />
      </Box>
    ),
    date: job.completionDate || job.creationDate,
    type: TaskType.LAUNCH,
  })), [jobs]);

  const downloadsMemo = useMemo(() => downloads.map((download) => ({
    name: (
      <Box className={classes.title}>
        {download.name}
      </Box>
    ),
    dateView: (
      <Box className={classes.dateblock}>
        {`(${t('downloads:expirationDate')} : ${convertUTCToLocalTime(download.expirationDate)})`}
      </Box>
    ),
    action: (
      download.failed ? (
        <InfoIcon className={classes.errorIcon} onClick={() => setMessageModalOpen(download.errorMessage)} />
      ) : (
        <Box>
          {download.ready ? (
            <DownloadLink url={getDownloadUrl(download.id)}>
              <FontAwesomeIcon size="lg" className={classes.downloadIcon} icon="download" />
            </DownloadLink>
          ) : <CircularProgress color="primary" style={{ width: '18px', height: '18px' }} />}
        </Box>
      )
    ),
    date: moment(download.expirationDate).subtract(1, 'days').format('YYYY-MM-DD HH:mm:ss'),
    type: TaskType.DOWNLOAD,
  })), [downloads]);

  const tasksMemo = useMemo(() => tasks.map((task) => ({
    name: (
      <Typography className={classes.title}>
        {task.name}
      </Typography>
    ),
    dateView: (
      <Box className={classes.dateblock}>
        <Box>
          <FontAwesomeIcon className={classes.dateicon} icon="calendar" />
          {convertUTCToLocalTime(task.creation_date_utc)}
        </Box>
        <Box>
          {task.completion_date_utc && (
            <>
              <FontAwesomeIcon className={classes.dateicon} icon="calendar-check" />
              {convertUTCToLocalTime(task.completion_date_utc)}
            </>
          )}
        </Box>
      </Box>
    ),
    action: (
      <Box>
        {
          !task.completion_date_utc &&
          <CircularProgress color="primary" style={{ width: '18px', height: '18px' }} />
        }
        {
          task.completion_date_utc && !task.result?.success && <InfoIcon className={classes.errorIcon} />
        }
      </Box>
    ),
    date: task.completion_date_utc || task.creation_date_utc,
    type: ((task.type === TaskType.COPY) && TaskType.COPY) || ((task.type === TaskType.ARCHIVE) && TaskType.ARCHIVE) || ((task.type === TaskType.UNARCHIVE) && TaskType.UNARCHIVE) || TaskType.COPY,
  })), [tasks]);

  const content = jobsMemo.concat(downloadsMemo.concat(tasksMemo));

  return (
    <Box className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && <JobTableView content={content || []} />}
      {openConfirmationModal && (
        <ConfirmationModal
          open={!!openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('singlestudy:confirmKill')}
          handleYes={() => killTask(openConfirmationModal)}
          handleNo={() => setOpenConfirmationModal(undefined)}
        />
      )}
      <LogModal
        isOpen={!!messageModalOpen}
        title={t('singlestudy:taskLog')}
        content={messageModalOpen}
        close={() => setMessageModalOpen(undefined)}
        style={{ width: '600px', height: '300px' }}
      />
    </Box>
  );
};

export default connector(JobsListing);
