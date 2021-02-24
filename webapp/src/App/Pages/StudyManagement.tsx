/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import debug from 'debug';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies } from '../../ducks/study';
import { getStudies } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import StudySearchTool from '../../components/StudySearchTool';

const logError = debug('antares:app:error');

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

const mapDispatch = ({
  loadStudies: initStudies,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const StudyManagement = (props: PropTypes) => {
  const { studies, loadStudies } = props;
  const classes = useStyles();
  const [loaded, setLoaded] = useState(true);
  const init = async () => {
    setLoaded(false);
    try {
      const allStudies = await getStudies();
      loadStudies(allStudies);
    } catch (e) {
      logError('woops', e);
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    init();
  }, []);


  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
        <StudySearchTool setLoading={(isLoading) => setLoaded(!isLoading)} />
      </div>
      {!loaded && <MainContentLoader />}
      {loaded && studies && <StudyListing studies={studies} />}
    </div>
  );
};

export default connector(StudyManagement);
