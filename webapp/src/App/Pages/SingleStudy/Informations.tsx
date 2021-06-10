import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import InformationView from './InformationView';
import TaskView from './TaskView';

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
  }
}));


interface PropTypes {
    studyId: string;
}

const Informations = (props: PropTypes) => {
  const { studyId } = props;
  const classes = useStyles();
  return (
    <div className={classes.root}>
        <InformationView studyId={studyId}/>
        <TaskView studyId={studyId} />
    </div>
  );
};

export default Informations;