import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { Box, createStyles, makeStyles, Theme } from '@material-ui/core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import ErrorIcon from '@material-ui/icons/Error';
import { getStudyJobLog } from '../../services/api/study';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import LogModal from '../ui/LogModal';
import { LaunchJob } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    logButtons: {
      display: 'flex',
    },
    logIcon: {
      cursor: 'pointer',
      margin: theme.spacing(0.5),
      color: theme.palette.primary.main,
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
    logError: {
      position: 'relative',
      cursor: 'pointer',
      margin: theme.spacing(0.5),
      '& svg:first-of-type': {
        color: theme.palette.primary.main,
      },
      '& svg:last-of-type': {
        position: 'absolute',
        bottom: -2,
        right: -3,
        fontSize: 12,
        color: theme.palette.secondary.main,
      },
      '&:hover': {
        '& svg:first-of-type': {
          color: theme.palette.secondary.main,
        },
        '& svg:last-of-type': {
          color: theme.palette.primary.main,
        },
      },
    },
  }));

interface PropsType {
  job: LaunchJob;
  logButton?: boolean;
  logErrorButton?: boolean;
}

const LogView = (props: PropsType) => {
  const { job, logButton, logErrorButton } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [jobIdDetail, setJobIdDetail] = useState<string>();
  const [followLogs, setFollowLogs] = useState<boolean>(false);
  const [logModalContent, setLogModalContent] = useState<string | undefined>();
  const [logModalContentLoading, setLogModalContentLoading] = useState<boolean>(false);

  const openLogView = (jobId: string, errorLogs = false) => {
    setJobIdDetail(jobId);
    setLogModalContentLoading(true);
    setFollowLogs(!errorLogs);
    (async () => {
      try {
        const logData = await getStudyJobLog(jobId, errorLogs ? 'STDERR' : 'STDOUT');
        setLogModalContent(logData);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failtofetchlogs'), e as AxiosError);
      } finally {
        setLogModalContentLoading(false);
      }
    })();
  };

  return (
    <Box className={classes.logButtons}>
      {logButton &&
        <FontAwesomeIcon size="lg" className={classes.logIcon} onClick={() => openLogView(job.id)} icon="file" />
      }
      {logErrorButton && (
      <Box className={classes.logError} onClick={() => openLogView(job.id, true)}>
        <FontAwesomeIcon size="lg" icon="file" />
        <ErrorIcon />
      </Box>
      )}
      <LogModal
        isOpen={!!jobIdDetail}
        title={t('singlestudy:taskLog')}
        followLogs={followLogs}
        jobId={jobIdDetail}
        content={logModalContent}
        loading={logModalContentLoading}
        close={() => setJobIdDetail(undefined)}
      />
    </Box>
  );
};

LogView.defaultProps = {
  logButton: false,
  logErrorButton: false,
};

export default LogView;
