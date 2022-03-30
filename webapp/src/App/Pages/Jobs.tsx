import React from 'react';
import { makeStyles, createStyles } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { addListener, removeListener } from '../../ducks/websockets';
import JobsListing from '../../components/JobsListing';

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      height: '100%',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      flexDirection: 'column',
      overflow: 'hidden',
      boxSizing: 'border-box',
    },
  }));

const mapState = () => ({});

const mapDispatch = {
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const Jobs = () => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <JobsListing />
    </div>
  );
};

export default connector(Jobs);
