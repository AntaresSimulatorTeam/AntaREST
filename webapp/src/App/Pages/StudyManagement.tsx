/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { makeStyles, createStyles, Button } from '@material-ui/core';
import ListIcon from '@material-ui/icons/List';
import ViewCompactIcon from '@material-ui/icons/ViewCompact';
import debug from 'debug';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies } from '../../ducks/study';
import { getStudies } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import StudySearchTool from '../../components/StudySearchTool';
import { StudyMetadata } from '../../common/types';
import { addListener, removeListener } from '../../ducks/websockets';
import theme from '../theme';

const logError = debug('antares:studymanagement:error');

const useStyles = makeStyles(() => createStyles({
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    borderBottom: '1px solid #d7d7d7',
  },
  view: {
    display: 'flex',
    flexFLow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    padding: '0px 10px',
  },
  viewButton: {
    color: theme.palette.primary.main,
  },
  viewIcon: {
    width: '35px',
    height: '35px',
  },
}));

const mapState = (state: AppState) => ({
  studies: state.study.studies,
});

const mapDispatch = ({
  loadStudies: initStudies,
  addWsListener: addListener,
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const StudyManagement = (props: PropTypes) => {
  const { studies, loadStudies, addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const [filteredStudies, setFilteredStudies] = useState<StudyMetadata[]>(studies);
  const [loaded, setLoaded] = useState(true);
  const [isList, setViewState] = useState(true);

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

  const listen = (ev: any) => {
    console.log(ev);
  };

  useEffect(() => {
    addWsListener(listen);
    init();
    return () => removeWsListener(listen);
  }, []);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
        <div className={classes.view}>
          <StudySearchTool setFiltered={setFilteredStudies} setLoading={(isLoading) => setLoaded(!isLoading)} />
          <Button
            className={classes.viewButton}
            onClick={() => setViewState(!isList)}
          >
            {
              isList ? <ViewCompactIcon className={classes.viewIcon} /> : <ListIcon className={classes.viewIcon} />
            }
          </Button>
        </div>
      </div>
      {!loaded && <MainContentLoader />}
      {loaded && studies && <StudyListing studies={filteredStudies} isList={isList} />}
    </div>
  );
};

export default connector(StudyManagement);
