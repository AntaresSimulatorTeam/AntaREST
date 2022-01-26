import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { addListener, removeListener } from '../../ducks/websockets';
import GenericTab from '../../components/JobListing/TabView';
import JobManagement from '../../components/JobListing/JobManagement';
import DownloadsManagement from '../../components/JobListing/DownloadsManagement';
import OtherJobManagement from '../../components/JobListing/OtherJobManagement';

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

interface MenuTab {
  [key: string]:
    () => JSX.Element;
}

const Jobs = () => {
  const classes = useStyles();
  const [navData, setNavData] = useState<MenuTab>({});

  useEffect(() => {
    const newNavData: {[key: string]: () => JSX.Element} = {
      jobs: () => <JobManagement />,
      exports: () => <DownloadsManagement />,
      others: () => <OtherJobManagement />,
    };
    setNavData(newNavData);
  }, []);

  return (
    <div className={classes.root}>
      <GenericTab items={navData} initialValue="jobs" />
    </div>
  );
};

export default connector(Jobs);
