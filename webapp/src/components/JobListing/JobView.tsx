import React, { useCallback, useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme, Paper, Typography, IconButton, useTheme } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import debug from 'debug';
import moment from 'moment';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown';
import ArrowDropUpIcon from '@material-ui/icons/ArrowDropUp';
import { AppState } from '../../App/reducers';
import { LaunchJob } from '../../common/types';
import { getStudyJobLog } from '../../services/api/study';
import { useNotif } from '../../services/utils';
import SimpleLoader from '../ui/loaders/SimpleLoader';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    flexDirection: 'column',
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(2),
  },
  jobs: {
    display: 'flex',
    flexWrap: 'wrap',
  },
  logs: {
    display: 'none',
    marginTop: theme.spacing(2),
    fontSize: '.8rem',
    whiteSpace: 'pre',
    padding: theme.spacing(1),
    maxHeight: '200px',
    overflowY: 'auto',
    position: 'relative',
    minHeight: '60px',
  },
  loaderContainer: {
    height: '100%', width: '100%', position: 'relative'
  },
  titleblock: {
    flexGrow: 1,
    display: 'flex',
    alignItems: 'center',
  },
  title: {
    color: theme.palette.primary.main,
  },
  dot: {
    width: '0.5em',
    height: '0.5em',
    borderRadius: '50%',
    marginRight: theme.spacing(1),
  },
  dateblock: {
    color: theme.palette.grey[500],
    fontSize: '0.85em',
  },
  dateicon: {
    marginRight: '0.5em',
  },
  dateandicon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '190px',
  },
}));

interface OwnProps {
  job: LaunchJob;
}

const mapState = (state: AppState, ownProps: OwnProps) => ({
  study: state.study.studies.find((s) => s.id === ownProps.job.studyId),
});

const mapDispatch = ({

});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnProps;

const JobView = (props: PropTypes) => {
  const { study, job } = props;
  const [t] = useTranslation();
  const theme = useTheme();
  const classes = useStyles();
  const createNotif = useNotif();
  const [logs, setLogs] = useState<string>();
  const [logLoading, setLogLoading] = useState(false);
  const [logView, setLogView] = useState<boolean>();

  const renderStatus = () => {
    let color = theme.palette.grey[400];
    if (job.status === 'JobStatus.SUCCESS') {
      color = theme.palette.success.main;
    } else if (job.status === 'JobStatus.FAILED') {
      color = theme.palette.error.main;
    } else if (job.status === 'JobStatus.RUNNING') {
      color = theme.palette.warning.main;
    }
    return (<div className={classes.dot} style={{ backgroundColor: color }} />);
  };

  const getLog = useCallback(async () => {
    try {
      setLogLoading(true);
      const jobLog = await getStudyJobLog(job.id);
      setLogs(jobLog);
    } catch (e) {
      logError('woops', e);
      createNotif(t('jobs:failedtoretrievelogs'), { variant: 'error' });
    } finally {
      setLogLoading(false);
    }
  }, [job, createNotif, t]);

  const renderLogView = () => {
    if (logView) {
      return (
        <Paper className={classes.logs} style={{ display: logView ? 'block' : 'none' }} variant="outlined">
          {logLoading ? <div className={classes.loaderContainer}><SimpleLoader /></div> : logs || t('jobs:logdetails')}
        </Paper>
      );
    }
    return <div />;
  };

  useEffect(() => {
    if (logView) {
      getLog();
    } else {
      setLogs(undefined);
    }
  }, [getLog, logView]);

  return (
    <Paper className={classes.root} elevation={1}>
      <div className={classes.jobs}>
        <div className={classes.titleblock}>
          {renderStatus()}
          {study && (
          <Link to={`/study/${encodeURI(study.id)}`}>
            <Typography className={classes.title}>
              {study.name}
            </Typography>
          </Link>
          )}
          {!study && (
          <Typography className={classes.title}>
            {t('main:unknown')}
          </Typography>
          )}
        </div>
        <div className={classes.dateandicon}>
          <div className={classes.dateblock}>
            <div>
              <FontAwesomeIcon className={classes.dateicon} icon="calendar" />
              {moment(job.creationDate).format('DD/MM/YY - HH:mm')}
            </div>
            <div>
              {job.completionDate && (
                <>
                  <FontAwesomeIcon className={classes.dateicon} icon="calendar-check" />
                  {moment(job.completionDate).format('DD/MM/YY - HH:mm')}
                </>
              )}
            </div>
          </div>
          <div>
            <IconButton onClick={() => setLogView(!logView)}>
              {logView ? <ArrowDropUpIcon /> : <ArrowDropDownIcon />}
            </IconButton>
          </div>
        </div>
      </div>
      {renderLogView()}
    </Paper>
  );
};

export default connector(JobView);
