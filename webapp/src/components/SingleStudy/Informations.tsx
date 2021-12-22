import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import InformationView from './InformationView';
import TaskView from './TaskView';
import NoteView from './NoteView';
import MapView from './MapView';
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
    overflow: 'hidden',
  },
  otherInfo: {
    flex: 1,
    height: '98%',
    minWidth: '350px',
    minHeight: '250px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
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
      <div className={classes.otherInfo}>
{/*       <NoteView studyId={study.id} />
        <TaskView jobs={jobs} />*/}
        <MapView studyId={study.id} />
      </div>
    </div>
  );
};

export default Informations;
