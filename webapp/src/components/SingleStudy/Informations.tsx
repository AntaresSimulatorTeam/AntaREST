import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import InformationView from './InformationView';
import TaskView from './TaskView';
import { LaunchJob, StudyMetadata } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    boxSizing: 'border-box',
    padding: theme.spacing(1),
    overflow: 'auto',
  },
}));

interface PropTypes {
    study: StudyMetadata;
    jobs: LaunchJob[];
}

const Informations = (props: PropTypes) => {
  const { study, jobs } = props;
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <InformationView study={study} />
      <TaskView jobs={jobs} />
    </div>
  );
};

export default Informations;
