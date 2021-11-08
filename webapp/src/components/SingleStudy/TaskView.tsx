/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React, { useState } from 'react';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  GridList,
  GridListTile,
  Button,
} from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { getStudyJobLog, killStudy } from '../../services/api/study';
import { LaunchJob } from '../../common/types';
import LogModal from '../ui/LogModal';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import ConfirmationModal from '../ui/ConfirmationModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '48%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      overflowY: 'auto',
      overflowX: 'hidden',
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    tasksList: {
      flex: 1,
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      overflowX: 'hidden',
      overflowY: 'auto',
    },
    task: {
      margin: theme.spacing(1),
      padding: theme.spacing(2),
      border: `1px solid ${theme.palette.primary.main}`,
      width: '80%',
    },
    message: {
      margin: theme.spacing(1),
      padding: theme.spacing(2),
      color: theme.palette.primary.main,
    },
    logButton: {
      cursor: 'pointer',
      textDecoration: 'underline',
      '&:hover': {
        textDecoration: 'none',
        color: theme.palette.secondary.main,
      },
    },
    gridList: {
      width: '100%',
    },
    gridTile: {
      width: '100%',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      color: theme.palette.primary.main,
    },
    label: {
      fontWeight: 'bold',
    },
    statusTile: {
      '& div': {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
      },
    },
    statusText: {
      display: 'block !important',
      width: 'auto !important',
    },
    killButtonHide: {
      display: 'none',
    },
  }));

interface PropTypes {
  jobs: LaunchJob[];
}

const TaskView = (props: PropTypes) => {
  const { jobs } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [jobIdDetail, setJobIdDetail] = useState<string>();
  const [jobIdKill, setJobIdKill] = useState<string>();
  const [logModalContent, setLogModalContent] = useState<string | undefined>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const openLogView = (jobId: string) => {
    (async () => {
      try {
        const logData = await getStudyJobLog(jobId);
        setLogModalContent(logData);
        setJobIdDetail(jobId);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failtofetchlogs'), e as AxiosError);
      }
    })();
  };
  const openConfirmModal = (jobId: string) => {
    setOpenConfirmationModal(true);
    setJobIdKill(jobId);
  };
  const killTask = (jobId: string) => {
    (async () => {
      try {
        await killStudy(jobId);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:failtokilltask'), e as AxiosError);
      }
      setOpenConfirmationModal(false);
    })();
  };

  return (
    <Paper className={classes.root}>
      <LogModal
        isOpen={!!jobIdDetail}
        title={t('singlestudy:taskLog')}
        jobId={jobIdDetail}
        content={logModalContent}
        close={() => setJobIdDetail(undefined)}
      />
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:currentTask')}</Typography>
      </div>
      <div className={classes.tasksList}>
        {jobs.length > 0 ? (
          jobs.map((item) => (
            <div className={classes.task} key={item.id}>
              <GridList cellHeight={50} className={classes.gridList}>
                <GridListTile className={classes.gridTile}>
                  <Typography className={classes.label}>{t('singlestudy:taskId')}</Typography>
                  <Typography>{item.id}</Typography>
                </GridListTile>
                <GridListTile className={`${classes.gridTile} ${classes.statusTile}`}>
                  <div className={classes.statusText}>
                    <Typography className={classes.label}>{t('singlestudy:taskStatus')}</Typography>
                    <Typography>{item.status}</Typography>
                  </div>
                  {item.status === 'running' ? <Button variant="contained" color="primary" onClick={() => openConfirmModal(item.id)}>{t('singlestudy:killStudy')}</Button> : <Button color="primary" variant="contained" className={classes.killButtonHide}>{t('singlestudy:killStudy')}</Button>}
                </GridListTile>
                <GridListTile className={classes.gridTile}>
                  <Typography className={classes.label}>
                    {t('singlestudy:taskCreationDate')}
                  </Typography>
                  <Typography>{item.creationDate}</Typography>
                </GridListTile>
                <GridListTile className={classes.gridTile}>
                  <Typography className={classes.label}>
                    {t('singlestudy:taskCompletionDate')}
                  </Typography>
                  <Typography>{item.completionDate}</Typography>
                </GridListTile>
                <GridListTile className={classes.gridTile}>
                  <Typography className={classes.label}>
                    {`${t('singlestudy:taskMessage')} / `}
                    <span onClick={() => openLogView(item.id)} className={classes.logButton}>
                      {t('singlestudy:taskLog')}
                    </span>
                  </Typography>
                  <Typography>{item.msg}</Typography>
                </GridListTile>
                <GridListTile className={classes.gridTile}>
                  <Typography className={classes.label}>{t('singlestudy:taskOutputId')}</Typography>
                  <Typography>{item.outputId}</Typography>
                </GridListTile>
              </GridList>
            </div>
          ))
        ) : (
          <div className={classes.message}>
            <Typography style={{ fontWeight: 'bold', fontSize: '1em' }}>
              {t('singlestudy:noTasks')}
            </Typography>
          </div>
        )}
        {openConfirmationModal && (
          <ConfirmationModal
            open={openConfirmationModal}
            title={t('main:confirmationModalTitle')}
            message={t('singlestudy:confirmKill')}
            handleYes={() => killTask(jobIdKill as string)}
            handleNo={() => setOpenConfirmationModal(false)}
          />
        )}
      </div>
    </Paper>
  );
};

export default TaskView;
