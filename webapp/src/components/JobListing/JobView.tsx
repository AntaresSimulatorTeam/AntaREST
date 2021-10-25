import React, { useEffect, useState } from 'react';
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
    width: '99%',
    display: 'flex',
    flexWrap: 'wrap',
  },
  logs: {
    display: 'none',
    marginTop: '10px',
    fontSize: '.8rem',
    whiteSpace: 'pre',
    padding: '10px 5px 10px 5px',
    maxHeight: '200px',
    overflowY: 'auto',
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

  const getLog = async () => {
    try {
      const JobLog = await getStudyJobLog(job.id);
      setLogs(JobLog);
    } catch (e) {
      logError('woops', e);
      createNotif(t('jobs:failedtoretrievelogs'), { variant: 'error' });
    }
  };

  const ToggleLogView = (view: boolean | undefined) => {
    if (view === true) {
      setLogView(false);
    } else {
      setLogView(true);
    }
  };

  const LogView = () => {
    let view;
    if (logView === true) {
      view = (
        <Paper className={classes.logs} style={{ display: 'block' }} variant="outlined">
          {logs != null ? logs : t('jobs:logdetails')}
        </Paper>
      );
    } else {
      view = (
        <Paper className={classes.logs} style={{ display: 'none' }} variant="outlined">
          {logs != null ? logs : t('jobs:logdetails')}
        </Paper>
      );
    }
    return view;
  };

  useEffect(() => {
    getLog();
  }, []);

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
            <IconButton onClick={() => ToggleLogView(logView)}>
              {logView === true ? <ArrowDropDownIcon /> : <ArrowDropUpIcon />}
            </IconButton>
          </div>
        </div>
      </div>
      {LogView()}
    </Paper>
  );
};

export default connector(JobView);
