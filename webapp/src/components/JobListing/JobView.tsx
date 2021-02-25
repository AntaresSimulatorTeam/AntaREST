import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme, Paper, Typography, useTheme } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import moment from 'moment';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { LaunchJob } from '../../services/api/study';
import { AppState } from '../../App/reducers';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    display: 'flex',
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(2),
    alignItems: 'center',
    flexWrap: 'wrap',
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

  return (
    <Paper className={classes.root} elevation={1}>
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
    </Paper>
  );
};

export default connector(JobView);
