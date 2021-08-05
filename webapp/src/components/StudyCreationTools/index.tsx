import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import CreateStudyForm from './CreateStudyForm';
import ImportStudyForm from './ImportStudyForm';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      margin: theme.spacing(3),
    },
  }));

const useFormStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(2),
      marginBottom: theme.spacing(2),
      display: 'flex',
      alignItems: 'center',
    },
    button: {
      width: '100px',
      border: `2px solid ${theme.palette.primary.main}`,
      fontWeight: 'bold',
    },
    input: {
      width: '200px',
      marginLeft: theme.spacing(2),
      marginRight: theme.spacing(2),
    },
  }));

const StudyCreationTools = () => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div>
        <CreateStudyForm useStyles={useFormStyles} />
      </div>
      <div>
        <ImportStudyForm useStyles={useFormStyles} />
      </div>
    </div>
  );
};

export default StudyCreationTools;
