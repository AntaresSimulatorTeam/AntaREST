import React, { useEffect, useState } from 'react';
import { makeStyles, Button, createStyles, Theme, Paper, Typography } from '@material-ui/core';
import FiberManualRecordIcon from '@material-ui/icons/FiberManualRecord';
import { useTheme } from '@material-ui/core/styles';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { Link } from 'react-router-dom';
import moment from 'moment';
import { JobStatus, LaunchJob, StudyMetadata } from '../../common/types';
import { getExportUrl, getStudyJobs } from '../../services/api/study';
import DownloadLink from '../ui/DownloadLink';
import ConfirmationModal from '../ui/ConfirmationModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    margin: theme.spacing(1),
    paddingRight: theme.spacing(1),
    paddingLeft: theme.spacing(1),
    width: '90%',
    height: '50px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  jobStatus: {
    width: '20px',
    height: '58%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
  },
  title: {
    color: theme.palette.primary.main,
    fontWeight: 'bold',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
  },
  id: {
    fontFamily: "'Courier', sans-serif",
    fontSize: 'small',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  info: {
    flex: 1,
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  buttons: {
    flex: 1,
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
}));

interface PropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
}

const StudyListSummaryView = (props: PropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { study, launchStudy, deleteStudy } = props;
  const [lastJobStatus, setLastJobsStatus] = useState<JobStatus | undefined>();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  const statusColor = {
    'JobStatus.RUNNING': 'orange',
    'JobStatus.PENDING': 'orange',
    'JobStatus.SUCCESS': 'green',
    'JobStatus.FAILED': 'red',
  };

  const deleteStudyAndCloseModal = () => {
    deleteStudy(study);
    setOpenConfirmationModal(false);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const jobList = await getStudyJobs(study.id);
        jobList.sort((a: LaunchJob, b: LaunchJob) => (moment(a.completionDate).isAfter(moment(b.completionDate)) ? -1 : 1));
        if (jobList.length > 0) setLastJobsStatus(jobList[0].status);
      } catch (e) {
        enqueueSnackbar(t('singlestudy:failtoloadjobs'), { variant: 'error' });
      }
    };
    init();
  }, [t, enqueueSnackbar, study.id]);

  return (
    <Paper className={classes.root}>
      {
         !!lastJobStatus && (
         <div className={classes.jobStatus}>
           <FiberManualRecordIcon style={{ width: '10px', height: '10px', color: statusColor[lastJobStatus] }} />
         </div>
         )}
      <div className={classes.info}>
        <Link className={classes.title} to={`/study/${encodeURI(study.id)}`}>
          <Typography className={classes.title} component="h3">
            {study.name}
          </Typography>
        </Link>
        <Typography color="textSecondary" className={classes.id}>
          {study.id}
        </Typography>
      </div>
      <div className={classes.buttons}>
        <Button size="small" style={{ color: theme.palette.secondary.main }} onClick={() => launchStudy(study)}>{t('main:launch')}</Button>
        <DownloadLink url={getExportUrl(study.id, false)}><Button size="small" style={{ color: theme.palette.primary.light }}>{t('main:export')}</Button></DownloadLink>
        <Button size="small" style={{ float: 'right', color: theme.palette.error.main }} onClick={() => setOpenConfirmationModal(true)}>{t('main:delete')}</Button>
      </div>
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('studymanager:confirmdelete')}
          handleYes={deleteStudyAndCloseModal}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </Paper>
  );
};

export default StudyListSummaryView;
