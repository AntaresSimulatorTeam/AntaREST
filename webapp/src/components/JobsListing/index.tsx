import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import moment from 'moment';
import JobView from '../JobListing/JobView';
import { LaunchJob } from '../../common/types';

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

const JobsListing = (props: PropTypes) => {
  const { jobs } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        {
          jobs
            .sort((a, b) => (moment(a.completionDate || a.creationDate).isAfter(moment(b.completionDate || b.creationDate)) ? -1 : 1))
            .reduce((prevVal, curVal) => { if (prevVal.find((el) => el.studyId === curVal.studyId)) { return prevVal; } return prevVal.concat([curVal]); }, [] as LaunchJob[])
            .map((job) => (
              <div key={job.id} className={classes.job}>
                <JobView job={job} />
              </div>
            ))}
      </div>
    </div>
  );
};

export default JobsListing;
