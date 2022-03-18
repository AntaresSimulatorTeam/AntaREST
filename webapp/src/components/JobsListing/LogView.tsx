import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { Box, createStyles, makeStyles, Theme, Button } from '@material-ui/core';
import { getStudyJobLog } from '../../services/api/study';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import LogModal from '../ui/LogModal';
import { LaunchJob } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {

    },
  }));

interface PropsType {
  job: LaunchJob;
  logButton?: string;
  logErrorButton?: string;
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
    <Box className={classes.root}>
      {!!logButton &&
        <Button onClick={() => openLogView(job.id)}>{logButton}</Button>
      }
      {!!logErrorButton &&
        <Button onClick={() => openLogView(job.id, true)}>{logErrorButton}</Button>
      }
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
  logButton: undefined,
  logErrorButton: undefined,
};

export default LogView;
