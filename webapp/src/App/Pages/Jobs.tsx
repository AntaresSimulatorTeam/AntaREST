import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { addListener, removeListener } from '../../ducks/websockets';
import GenericTab from '../../components/JobListing/TabView';
import Jobs from '../../components/JobListing/JobManagement';
import DownloadsManagement from '../../components/JobListing/DownloadsManagement';

const useStyles = makeStyles((theme: Theme) =>
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
    breadcrumbs: {
      backgroundColor: '#d7d7d7',
      width: '100%',
      padding: theme.spacing(1),
    },
    breadcrumbsfirstelement: {
      marginLeft: theme.spacing(1),
    },
    dot: {
      height: '0.5em',
      width: '0.5em',
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

const JobManagement = () => {
  const classes = useStyles();
  const [navData, setNavData] = useState<MenuTab>({});

  useEffect(() => {
    const newNavData: {[key: string]: () => JSX.Element} = {
      jobs: () => <Jobs />,
      exports: () => <DownloadsManagement />,
      others: () => <div style={{ width: '100%', height: '100%', backgroundColor: 'green' }} />,
    };
    setNavData(newNavData);
  }, []);

  return (
    <div className={classes.root}>
      <GenericTab items={navData} initialValue="jobs" />
    </div>
  );
};

export default connector(JobManagement);
