import React from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import { AppState } from '../../reducers';
import StudyCreationTools from '../../../components/StudyCreationTools';
import StudyListing from '../../../components/StudyListing';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    borderBottom: '1px solid #d7d7d7',
  },
}));

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const connector = connect(mapState, {});
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const StudyManagement = (props: PropTypes) => {
  const { studies } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
      </div>
      {studies && <StudyListing studies={studies} />}
    </div>
  );
};

export default connector(StudyManagement);
