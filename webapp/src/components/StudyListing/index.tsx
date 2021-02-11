import React from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import StudyBlockSummaryView from './StudyBlockSummaryView.tsx';
import { StudyMetadata } from '../../common/types';

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
}));

interface PropTypes {
  studies: StudyMetadata[];
}

const StudyListing = (props: PropTypes) => {
  const classes = useStyles();
  const { studies } = props;
  return (
    <div className={classes.root}>
      <div className={classes.container}>
        {
          studies.map((s) => (<StudyBlockSummaryView key={s.id} study={s} />))
        }
      </div>
    </div>
  );
};

export default StudyListing;
