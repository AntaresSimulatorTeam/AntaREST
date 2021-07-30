/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { makeStyles, createStyles, Tooltip, Button } from '@material-ui/core';
import ListIcon from '@material-ui/icons/List';
import ViewCompactIcon from '@material-ui/icons/ViewCompact';
import RefreshIcon from '@material-ui/icons/Refresh';
import SortByAlphaIcon from '@material-ui/icons/SortByAlpha';
import DateRangeIcon from '@material-ui/icons/DateRange';
import debug from 'debug';
import moment from 'moment';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies, addStudies, removeStudies } from '../../ducks/study';
import { getStudies, getStudyMetadata } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import SortView from '../../components/ui/SortView';
import { SortItem } from '../../components/ui/SortView/utils';
import StudySearchTool from '../../components/StudySearchTool';
import { StudyMetadata, StudySummary, WSEvent, WSMessage } from '../../common/types';
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
  addStudy: (study: StudyMetadata) => addStudies([study]),
  deleteStudy: (id: string) => removeStudies([id]),
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const StudyManagement = (props: PropTypes) => {
  const { studies, addStudy, deleteStudy, loadStudies, addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [filteredStudies, setFilteredStudies] = useState<StudyMetadata[]>(studies);
  const [loaded, setLoaded] = useState(true);
  const [isList, setViewState] = useState(true);
  const [currentSortItem, setCurrentSortItem] = useState<SortItem>();

  const sortList = [{ id: t('studymanager:sortByName'), elm: () => <SortByAlphaIcon /> },
    { id: t('studymanager:sortByDate'), elm: () => <DateRangeIcon /> }];

  const sortStudies = (sortItem: SortItem) => {
    const tmpStudies: Array<StudyMetadata> = ([] as Array<StudyMetadata>).concat(filteredStudies);
    if (sortItem.status !== 'NONE') {
      tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
        const firstElm = sortItem.status === 'INCREASE' ? studyA : studyB;
        const secondElm = sortItem.status === 'INCREASE' ? studyB : studyA;
        if (sortItem.element.id === sortList[0].id) {
          return firstElm.name.localeCompare(secondElm.name);
        }
        return (moment(firstElm.modificationDate).isAfter(moment(secondElm.modificationDate)) ? -1 : 1);
      });
      setFilteredStudies(tmpStudies);
    } else {
      setFilteredStudies(studies);
    }
    setCurrentSortItem(sortItem);
  };

  const getAllStudies = async (refresh: boolean) => {
    if (currentSortItem) {
      sortStudies(currentSortItem);
    }
    setLoaded(false);
    try {
      if (studies.length === 0 || refresh) {
        const allStudies = await getStudies();
        loadStudies(allStudies);

        if (currentSortItem) {
          setFilteredStudies(allStudies);
          sortStudies(currentSortItem);
        }
      }
    } catch (e) {
      logError('woops', e);
    } finally {
      setLoaded(true);
    }
  };

  const listen = async (ev: WSMessage) => {
    const studySummary = ev.payload as StudySummary;
    switch (ev.type) {
      case WSEvent.STUDY_CREATED:
        addStudy(await getStudyMetadata(studySummary.id));
        break;
      case WSEvent.STUDY_DELETED:
        deleteStudy(studySummary.id);
        break;
      case WSEvent.STUDY_EDITED:
        addStudy(await getStudyMetadata(studySummary.id));
        break;

      default:
        break;
    }
    console.log(ev);
  };

  useEffect(() => {
    addWsListener(listen);
    getAllStudies(false);
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
            <Button
              color="primary"
              onClick={() => getAllStudies(true)}
            >
              <RefreshIcon />
            </Button>
          </Tooltip>
          <Button
            color="primary"
            onClick={() => setViewState(!isList)}
          >
            {isList ? <ViewCompactIcon /> : <ListIcon />}
          </Button>
        </div>
      </div>
      {!loaded && <MainContentLoader />}
      {loaded && studies && <StudyListing studies={filteredStudies} isList={isList} />}
    </div>
  );
};

export default connector(StudyManagement);
