/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { connect, ConnectedProps } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { makeStyles, createStyles, Tooltip, Button, Checkbox, Typography } from '@material-ui/core';
import ListIcon from '@material-ui/icons/List';
import ViewCompactIcon from '@material-ui/icons/ViewCompact';
import RefreshIcon from '@material-ui/icons/Refresh';
import SortByAlphaIcon from '@material-ui/icons/SortByAlpha';
import DateRangeIcon from '@material-ui/icons/DateRange';
import debug from 'debug';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies, addStudies, removeStudies } from '../../ducks/study';
import { getStudies, getStudyMetadata } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import SortView from '../../components/ui/SortView';
import { SortItem } from '../../components/ui/SortView/utils';
import StudySearchTool from '../../components/StudySearchTool';
import { StudyMetadata, StudySummary, WSEvent, WSMessage, UserDTO, GroupDTO } from '../../common/types';
import AutoCompleteView from '../../components/StudySearchTool/AutoCompleteView';
import { addListener, removeListener } from '../../ducks/websockets';
import theme from '../theme';
import { getGroups, getUsers } from '../../services/api/user';

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
    marginBottom: theme.spacing(1),
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
  user: state.auth.user,
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
  const { user, studies, addStudy, deleteStudy, loadStudies, addWsListener, removeWsListener } = props;
  const classes = useStyles();
  const [t] = useTranslation();
  const [filteredStudies, setFilteredStudies] = useState<Array<StudyMetadata>>(studies);
  const [loaded, setLoaded] = useState(true);
  const [isList, setViewState] = useState(true);
  const [managedFilter, setManageFilter] = useState<boolean>(false);
  const [currentSortItem, setCurrentSortItem] = useState<SortItem>();

  const sortList = [{ id: t('studymanager:sortByName'), elm: () => <SortByAlphaIcon /> },
    { id: t('studymanager:sortByDate'), elm: () => <DateRangeIcon /> }];

  const getAllStudies = async (refresh: boolean) => {
    setLoaded(false);
    try {
      if (studies.length === 0 || refresh) {
        const allStudies = await getStudies();
        loadStudies(allStudies);
      }
    } catch (e) {
      logError('woops', e);
    } finally {
      setLoaded(true);
    }
  };

  const [userList, setUserList] = useState<Array<UserDTO>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [currentUser, setCurrentUser] = useState<UserDTO>();
  const [currentGroup, setCurrentGroup] = useState<GroupDTO>();

  const init = async () => {
    try {
      const userRes = await getUsers();
      setUserList(userRes);
      if (user) {
        setCurrentUser(userRes.find((elm) => elm.id === user.id));
      }

      const groupRes = await getGroups();
      setGroupList(groupRes);
    } catch (error) {
      console.log(error);
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
    init();
    getAllStudies(false);
    return () => removeWsListener(listen);
  }, []);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
        <StudySearchTool filterManaged={managedFilter} userFilter={currentUser} groupFilter={currentGroup} sortList={sortList} sortItem={currentSortItem} setFiltered={setFilteredStudies} setLoading={(isLoading) => setLoaded(!isLoading)} />
        <div className={classes.view}>
          <div className={classes.view} style={{ marginBottom: 0 }}>
            <Checkbox
              checked={managedFilter}
              onChange={() => setManageFilter(!managedFilter)}
              inputProps={{ 'aria-label': 'primary checkbox' }}
            />
            <Typography>
              {t('studymanager:managedStudiesFilter')}
            </Typography>
          </div>
          <AutoCompleteView label={t('studymanager:userFilter')} value={currentUser} list={userList} setValue={(elm) => setCurrentUser(elm as (UserDTO | undefined))} />
          <AutoCompleteView label={t('studymanager:groupFilter')} value={currentGroup} list={groupList} setValue={(elm) => setCurrentGroup(elm as (GroupDTO | undefined))} />
          <SortView itemNames={sortList} onClick={(item: SortItem) => setCurrentSortItem({ ...item })} />
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
