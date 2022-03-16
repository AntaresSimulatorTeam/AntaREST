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

/*
import React, { useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Breadcrumbs } from '@material-ui/core';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { addListener, removeListener } from '../../ducks/websockets';
import GenericTab from '../../components/JobListing/TabView';
import JobManagement from '../../components/JobListing/JobManagement';
import DownloadsManagement from '../../components/JobListing/DownloadsManagement';
import OtherJobManagement from '../../components/JobListing/OtherJobManagement';

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
  const [t] = useTranslation();

  useEffect(() => {
    const newNavData: {[key: string]: () => JSX.Element} = {
      launches: () => <JobManagement />,
      exports: () => <DownloadsManagement />,
      others: () => <OtherJobManagement />,
    };
    setNavData(newNavData);
  }, []);

  return (
    <div className={classes.root}>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        <Link to="/" className={classes.breadcrumbsfirstelement}>
          {t('main:allStudies')}
        </Link>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {t('main:jobs')}
        </div>
      </Breadcrumbs>
      <GenericTab items={navData} initialValue="launches" />
    </div>
  );
};

export default connector(Jobs);
*/
