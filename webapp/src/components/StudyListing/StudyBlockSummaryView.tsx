import React, { useEffect, useState } from 'react';
import clsx from 'clsx';
import moment from 'moment';
import { makeStyles, Button, createStyles, Theme, Card, CardContent, Typography, Grid, CardActions } from '@material-ui/core';
import FiberManualRecordIcon from '@material-ui/icons/FiberManualRecord';
import { useTheme } from '@material-ui/core/styles';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { JobStatus, LaunchJob, StudyMetadata } from '../../common/types';
import { getExportUrl, getStudyJobs } from '../../services/api/study';
import DownloadLink from '../ui/DownloadLink';
import ConfirmationModal from '../ui/ConfirmationModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    margin: '10px',
    padding: '4px',
    width: '400px',
    height: '170px',
  },
  jobStatus: {
    width: '20px',
    marginLeft: theme.spacing(1),
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
  },
  buttons: {
    width: '100%',
  },
  title: {
    color: theme.palette.primary.main,
    fontWeight: 'bold',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
  },
  managed: {
    backgroundColor: theme.palette.secondary.main,
  },
  titleContainer: {
    display: 'flex',
    alignItems: 'center',
  },
  workspace: {
    marginLeft: theme.spacing(1),
  },
  workspaceBadge: {
    border: `1px solid ${theme.palette.primary.main}`,
    borderRadius: '4px',
    padding: '0 4px',
    fontSize: '0.8em',
  },
  id: {
    fontFamily: "'Courier', sans-serif",
    fontSize: 'small',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  info: {
    marginTop: theme.spacing(1),
  },
  infotxt: {
    marginLeft: theme.spacing(1),
  },
  pos: {
    marginBottom: 12,
  },
}));

interface PropTypes {
  study: StudyMetadata;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
}

const StudyBlockSummaryView = (props: PropTypes) => {
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
    <div>
      <Card className={classes.root}>
        <CardContent>
          <div className={classes.titleContainer}>
            <Link className={classes.title} to={`/study/${encodeURI(study.id)}`}>
              <Typography className={classes.title} component="h3">
                {study.name}
                {
                  !!lastJobStatus && (
                  <span className={classes.jobStatus}>
                    <FiberManualRecordIcon style={{ width: '15px', height: '15px', color: statusColor[lastJobStatus] }} />
                  </span>
                  )
                }
              </Typography>
            </Link>
            <div className={classes.workspace}>
              <div className={clsx(classes.workspaceBadge, study.managed ? classes.managed : {})}>
                {study.workspace}
              </div>
            </div>
          </div>
          <Typography color="textSecondary" className={classes.id} gutterBottom>
            {study.id}
          </Typography>
          <Grid container spacing={2} className={classes.info}>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="user" />
              <span className={classes.infotxt}>{study.author}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="clock" />
              <span className={classes.infotxt}>{moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm')}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="code-branch" />
              <span className={classes.infotxt}>{study.version}</span>
            </Grid>
            <Grid item xs={6}>
              <FontAwesomeIcon icon="history" />
              <span className={classes.infotxt}>{moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm')}</span>
            </Grid>
          </Grid>
        </CardContent>
        <CardActions>
          <div className={classes.buttons}>
            <Button size="small" style={{ color: theme.palette.secondary.main }} onClick={() => launchStudy(study)}>{t('main:launch')}</Button>
            <DownloadLink url={getExportUrl(study.id, false)}><Button size="small" style={{ color: theme.palette.primary.light }}>{t('main:export')}</Button></DownloadLink>
          </div>
          <Button size="small" style={{ float: 'right', color: theme.palette.error.main }} onClick={() => setOpenConfirmationModal(true)}>{t('main:delete')}</Button>
        </CardActions>
        {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('studymanager:confirmdelete')}
          handleYes={deleteStudyAndCloseModal}
          handleNo={() => setOpenConfirmationModal(false)}
        />
        )}
      </Card>
    </div>
  );
};

export default StudyBlockSummaryView;
