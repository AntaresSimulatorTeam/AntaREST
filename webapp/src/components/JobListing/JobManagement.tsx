/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import debug from 'debug';
import { useTranslation } from 'react-i18next';
import { createStyles, makeStyles } from '@material-ui/core';
import { AppState } from '../../App/reducers';
import { getStudyJobs, getStudies } from '../../services/api/study';
import JobListing from '.';
import { useNotif } from '../../services/utils';
import MainContentLoader from '../ui/loaders/MainContentLoader';
import { initStudies } from '../../ducks/study';
import { LaunchJob } from '../../common/types';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles(() => createStyles({
  root: {
    width: '100%',
    flex: 1,
    overflowY: 'auto',
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

const mapDispatch = ({
  loadStudies: initStudies,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const JobManagement = (props: PropTypes) => {
  const { studies, loadStudies } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [jobs, setJobs] = useState<LaunchJob[]>();
  const createNotif = useNotif();
  const [loaded, setLoaded] = useState(true);

  const init = async () => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        const allStudies = await getStudies();
        loadStudies(allStudies);
      }
      const allJobs = await getStudyJobs(undefined, false);
      setJobs(allJobs);
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

export default connector(JobManagement);
