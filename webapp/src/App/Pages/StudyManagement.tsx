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
import { useSnackbar } from 'notistack';
import { AppState } from '../reducers';
import StudyCreationTools from '../../components/StudyCreationTools';
import StudyListing from '../../components/StudyListing';
import { initStudies } from '../../ducks/study';
import { getStudies } from '../../services/api/study';
import MainContentLoader from '../../components/ui/loaders/MainContentLoader';
import SortView from '../../components/ui/SortView';
import { SortItem } from '../../components/ui/SortView/utils';
import StudySearchTool from '../../components/StudySearchTool';
import { StudyMetadata, UserDTO, GroupDTO, GenericInfo } from '../../common/types';
import AutoCompleteView from '../../components/StudySearchTool/AutoCompleteView';
import theme from '../theme';
import { getGroups, getUsers } from '../../services/api/user';
import { loadState, saveState } from '../../services/utils/localStorage';
import enqueueErrorSnackbar from '../../components/ui/ErrorSnackBar';
import { AxiosError } from 'axios';

const logError = debug('antares:studymanagement:error');

const DEFAULT_LIST_MODE_KEY = 'studylisting.listmode';
const DEFAULT_FILTER_USER = 'studylisting.filter.user';
const DEFAULT_FILTER_GROUP = 'studylisting.filter.group';
const DEFAULT_FILTER_VERSION = 'studylisting.filter.version';
const DEFAULT_FILTER_MANAGED = 'studylisting.filter.managed';
const DEFAULT_FILTER_SORTING = 'studylisting.filter.sorting';

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
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [filteredStudies, setFilteredStudies] = useState<Array<StudyMetadata>>(studies);
  const [loaded, setLoaded] = useState(true);
  const [isList, setViewState] = useState(loadState<boolean>(DEFAULT_LIST_MODE_KEY, true));
  const [managedFilter, setManageFilter] = useState(loadState<boolean>(DEFAULT_FILTER_MANAGED, false));
  const [currentSortItem, setCurrentSortItem] = useState<SortItem|undefined>(loadState<SortItem>(DEFAULT_FILTER_SORTING));

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
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoretrievestudies'), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const [userList, setUserList] = useState<Array<UserDTO>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [currentUser, setCurrentUser] = useState<UserDTO|undefined>(loadState<UserDTO>(DEFAULT_FILTER_USER));
  const [currentGroup, setCurrentGroup] = useState<GroupDTO|undefined>(loadState<GroupDTO>(DEFAULT_FILTER_GROUP));
  const [currentVersion, setCurrentVersion] = useState<GenericInfo|undefined>(loadState<GenericInfo>(DEFAULT_FILTER_VERSION));

  const versionList = [{ id: '640', name: '6.4.0' },
    { id: '700', name: '7.0.0' },
    { id: '710', name: '7.1.0' },
    { id: '720', name: '7.2.0' },
    { id: '800', name: '8.0.0' }];

  const init = async () => {
    try {
      const userRes = await getUsers();
      setUserList(userRes);

      const groupRes = await getGroups();
      setGroupList(groupRes);
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    init();
    getAllStudies(false);
  }, []);

  useEffect(() => {
    saveState(DEFAULT_LIST_MODE_KEY, isList);
    saveState(DEFAULT_FILTER_USER, currentUser);
    saveState(DEFAULT_FILTER_GROUP, currentGroup);
    saveState(DEFAULT_FILTER_MANAGED, managedFilter);
    saveState(DEFAULT_FILTER_VERSION, currentVersion);
    saveState(DEFAULT_FILTER_SORTING, currentSortItem);
  }, [isList, currentVersion, currentUser, currentGroup, currentSortItem, managedFilter]);

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <StudyCreationTools />
        <StudySearchTool filterManaged={!!managedFilter} versionFilter={currentVersion} userFilter={currentUser} groupFilter={currentGroup} sortList={sortList} sortItem={currentSortItem} setFiltered={setFilteredStudies} setLoading={(isLoading) => setLoaded(!isLoading)} />
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
          <AutoCompleteView label={t('studymanager:versionFilter')} value={currentVersion} list={versionList} setValue={(elm) => setCurrentVersion(elm as (GenericInfo | undefined))} />
          <AutoCompleteView label={t('studymanager:userFilter')} value={currentUser} list={userList} setValue={(elm) => setCurrentUser(elm as (UserDTO | undefined))} />
          <AutoCompleteView label={t('studymanager:groupFilter')} value={currentGroup} list={groupList} setValue={(elm) => setCurrentGroup(elm as (GroupDTO | undefined))} />
          <SortView itemNames={sortList} defaultValue={currentSortItem} onClick={(item: SortItem) => setCurrentSortItem({ ...item })} />
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
            onClick={() => {
              setViewState(!isList);
            }}
          >
            {isList ? <ViewCompactIcon /> : <ListIcon />}
          </Button>
        </div>
      </div>
      {!loaded && <MainContentLoader />}
      {loaded && studies && <StudyListing studies={filteredStudies} isList={!!isList} />}
    </div>
  );
};

export default connector(StudyManagement);
