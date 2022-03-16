/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect, ReactNode } from 'react';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import debug from 'debug';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import moment from 'moment';
import { makeStyles, createStyles, Theme, useTheme, Typography, Box } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import BlockIcon from '@material-ui/icons/Block';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import JobTableView from './JobTableView';
import { convertUTCToLocalTime, useNotif } from '../../services/utils';
import { AppState } from '../../App/reducers';
import { downloadJobOutput, killStudy, getStudyJobs, getStudies } from '../../services/api/study';
import { initStudies } from '../../ducks/study';
import { LaunchJob } from '../../common/types';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import ConfirmationModal from '../ui/ConfirmationModal';

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
  },
  dateblock: {
    color: theme.palette.grey[500],
    fontSize: '0.85em',
  },
  dateicon: {
    marginRight: '0.5em',
  },
  killButtonHide: {
    display: 'none',
  },
  dot: {
    width: '0.5em',
    height: '0.5em',
    borderRadius: '50%',
    marginRight: theme.spacing(1),
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
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

interface JobsType {
    name: ReactNode;
    date: ReactNode;
    action: ReactNode;
}

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
  loadStudies: initStudies,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const JobsListing = (props: PropTypes) => {
  const { studies, loadStudies } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [jobs, setJobs] = useState<LaunchJob[]>();
  const [content, setContent] = useState<Array<JobsType>>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(false);
  const [openConfirmationModal, setOpenConfirmationModal] = useState<string | undefined>();

  const init = async () => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        const allStudies = await getStudies();
        loadStudies(allStudies);
      }
      const allJobs = await getStudyJobs(undefined, false);
      setJobs(allJobs);
    } catch (e) {
      logError('woops', e);
      createNotif(t('jobs:failedtoretrievejobs'), { variant: 'error' });
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
    return (<div className={classes.dot} style={{ backgroundColor: color }} />);
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
    init();
  }, []);

  useEffect(() => {
    if (jobs) {
      const tab = jobs
        .sort((a, b) => (moment(a.completionDate || a.creationDate).isAfter(moment(b.completionDate || b.creationDate)) ? -1 : 1))
        .reduce((prevVal, curVal) => { if (prevVal.find((el) => el.studyId === curVal.studyId)) { return prevVal; } return prevVal.concat([curVal]); }, [] as LaunchJob[])
        .map((job) => ({
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
          date: (
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
            <Box>
              <Box className={classes.actionButton}>
                {job.status === 'running' ? <BlockIcon className={classes.blockIcon} onClick={() => setOpenConfirmationModal(job.id)} /> : <Box />}
              </Box>
              <Box>
                {job.status === 'success' ? <FontAwesomeIcon className={classes.downloadIcon} icon="download" onClick={() => exportJobOutput(job.id)} /> : <Box />}
              </Box>
            </Box>
          ),
        }));
      setContent(tab);
    }
  }, [jobs]);

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
    </Box>
  );
};

export default connector(JobsListing);
