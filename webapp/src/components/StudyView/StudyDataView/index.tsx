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
  study: string;
  type: 'json' | 'file';
  data: string;
}

const StudyDataView = (props: PropTypes) => {
  const { study, type, data } = props;
  const classes = useStyles();

  const renderData = () => {
    if (type === 'file') {
      return <StudyFileView study={study} url={data} />;
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
