import React from 'react';
import { Paper, makeStyles, Theme, createStyles } from '@material-ui/core';
import StudyFileView from './StudyFileView';
import StudyJsonView from './StudyJsonView';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    padding: theme.spacing(2),
    overflow: 'auto',
    flexGrow: 1,
  },
}));

interface PropTypes {
  type: 'json' | 'file';
  data: string;
}

const StudyDataView = (props: PropTypes) => {
  const { type, data } = props;
  const classes = useStyles();

  const renderData = () => {
    if (type === 'file') {
      return <StudyFileView url={data} />;
    }
    return <StudyJsonView data={data} />;
  };

  return (
    <Paper className={classes.root}>
      {renderData()}
    </Paper>
  );
};

export default StudyDataView;
