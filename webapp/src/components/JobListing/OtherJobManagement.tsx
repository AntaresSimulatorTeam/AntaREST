/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import debug from 'debug';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles, Theme, Breadcrumbs } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { AppState } from '../../App/reducers';
import { getStudyJobs, getStudies } from '../../services/api/study';
import JobListing from '.';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import { initStudies } from '../../ducks/study';
import { LaunchJob } from '../../common/types';
import { getAllMiscRunningTasks } from '../../services/api/tasks';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  breadcrumbs: {
    backgroundColor: '#d7d7d7',
    padding: theme.spacing(1),
  },
  header: {
    borderBottom: '1px solid #d7d7d7',
  },
}));

const OtherJobManagement = () => {
  const classes = useStyles();
  const [t] = useTranslation();
  const [jobs, setJobs] = useState<LaunchJob[]>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(true);

  const init = async () => {
    setLoaded(false);
    try {
      const allJobs = await getAllMiscRunningTasks();
      //setJobs(allJobs);
    } catch (e) {
      logError('woops', e);
      createNotif(t('jobs:failedtoretrievejobs'), { variant: 'error' });
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    init();
  }, []);

  return (
    <div className={classes.root}>
      {!loaded && <MainContentLoader />}
      {loaded && jobs && <JobListing jobs={jobs} />}
    </div>
  );
};

export default OtherJobManagement;
