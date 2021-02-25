import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import moment from 'moment';
import { LaunchJob } from '../../services/api/study';
import JobView from './JobView';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flexGrow: 1,
    overflow: 'auto',
  },
  container: {
    display: 'flex',
    width: '100%',
    flexWrap: 'wrap',
    paddingTop: theme.spacing(2),
    justifyContent: 'space-around',
  },
  job: {
    marginLeft: theme.spacing(3),
    marginRight: theme.spacing(3),
    marginBottom: theme.spacing(1),
    width: '100%',
  },
}));

interface PropTypes {
  jobs: LaunchJob[];
}

const JobListing = (props: PropTypes) => {
  const { jobs } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        {
          jobs
            .sort((a, b) => (moment(a.completionDate).isAfter(moment(b.completionDate)) ? -1 : 1))
            .map((job) => (
              <div key={job.id} className={classes.job}>
                <JobView job={job} />
              </div>
            ))}
      </div>
    </div>
  );
};

export default JobListing;
