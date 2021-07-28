/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { makeStyles, createStyles, Tooltip } from '@material-ui/core';
import ListIcon from '@material-ui/icons/List';
import ViewCompactIcon from '@material-ui/icons/ViewCompact';
import RefreshIcon from '@material-ui/icons/Refresh';
import debug from 'debug';
import moment from 'moment';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies } from '../../ducks/study';
import { getStudies } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import SortView from '../../components/ui/SortView';
import { SortItem } from '../../components/ui/SortView/utils';
import StudySearchTool from '../../components/StudySearchTool';
import { StudyMetadata, WSMessage } from '../../common/types';
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
  icon: {
    width: '24px',
    height: '24px',
    cursor: 'pointer',
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
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
  const [t] = useTranslation();
  const [filteredStudies, setFilteredStudies] = useState<StudyMetadata[]>(studies);
  const [loaded, setLoaded] = useState(true);
  const [isList, setViewState] = useState(true);
  const [currentSortItem, setCurrentSortItem] = useState<SortItem>();

  const sortList = [t('studymanager:sortByName'), t('studymanager:sortByDate')];

  const sortStudies = (sortItem: SortItem) => {
    const tmpStudies: Array<StudyMetadata> = ([] as Array<StudyMetadata>).concat(filteredStudies);
    if (sortItem.status !== 'NONE') {
      tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
        const firstElm = sortItem.status === 'INCREASE' ? studyA : studyB;
        const secondElm = sortItem.status === 'INCREASE' ? studyB : studyA;
        if (sortItem.name === sortList[0]) {
          return firstElm.name.localeCompare(secondElm.name);
        }
        return (moment(firstElm.modificationDate).isAfter(moment(secondElm.modificationDate)) ? -1 : 1);
      });
    }
    setFilteredStudies(tmpStudies);
    setCurrentSortItem(sortItem);
  };

  const getAllStudies = async () => {
    const allStudies = await getStudies();
    loadStudies(allStudies);

    if (currentSortItem) {
      sortStudies(currentSortItem);
    }
  };
  const init = async () => {
    setLoaded(false);
    try {
      if (studies.length === 0) {
        await getAllStudies();
      }
    } catch (e) {
      logError('woops', e);
    } finally {
      setLoaded(true);
    }
  };

  const listen = (ev: WSMessage) => {
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
          <SortView itemNames={sortList} onClick={(item: SortItem) => sortStudies(item)} />
          <Tooltip title={t('studymanager:refresh') as string} style={{ marginRight: theme.spacing(0.5) }}>
            <RefreshIcon className={classes.icon} onClick={() => getAllStudies()} />
          </Tooltip>
          {
              isList ? (
                <ViewCompactIcon
                  className={classes.icon}
                  onClick={() => setViewState(!isList)}
                />
              ) : <ListIcon className={classes.icon} onClick={() => setViewState(!isList)} />
            }
        </div>
      </div>
      {!loaded && <MainContentLoader />}
      {loaded && studies && <StudyListing studies={filteredStudies} isList={isList} />}
    </div>
  );
};

export default connector(StudyManagement);
