import React, { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import { connect, ConnectedProps } from 'react-redux';
import { initStudies, initStudiesVersion } from '../../store/study';
import { AppState } from '../../store/reducers';
import { GenericInfo, GroupDTO, StudyMetadata, UserDTO } from '../../common/types';
import { loadState, saveState } from '../../services/utils/localStorage';
import { convertVersions } from '../../services/utils';
import { getGroups, getUsers } from '../../services/api/user';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';

const mapState = (state: AppState) => ({
    studies: state.study.studies,
    versions: state.study.versionList,
  });
  
  const mapDispatch = ({
    loadStudies: initStudies,
    loadVersions: initStudiesVersion,
  });
  
  const connector = connect(mapState, mapDispatch);
  type ReduxProps = ConnectedProps<typeof connector>;
  type PropTypes = ReduxProps;

const StudiesList = (props: PropTypes) => {
    const { studies, loadStudies, loadVersions, versions } = props;
    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const [filteredStudies, setFilteredStudies] = useState<Array<StudyMetadata>>(studies);
    const [dirViewStudiesNb, setDirViewStudiesNb] = useState<number>(-1);
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

  const versionList = convertVersions(versions || []);

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
    if (!versions) {
      loadVersions();
    }
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
    <Box flex={1} height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center"
    boxSizing="border-box" sx={{ overflowX: 'hidden',overflowY: 'auto' }}>
        BONJOUR
    </Box>  
  );
}

export default StudiesList;
