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
  const [loaded, setLoaded] = useState(studies.length !== 0);

  const init = async () => {
    if (studies.length === 0) {
      try {
        const allStudies = await getStudies();
        loadStudies(allStudies);
        setLoaded(true);
      } catch (e) {
        logError('woops', e);
      }
    }
  };

  useEffect(() => {
    init();
  }, []);


  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
      </div>
      {!loaded && <MainContentLoader />}
      {studies && <StudyListing studies={studies} />}
    </div>
  );
};

export default connector(StudyManagement);
