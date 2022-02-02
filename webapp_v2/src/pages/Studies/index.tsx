import React, { useEffect, useState } from 'react';
import { styled, useTheme } from '@mui/material/styles';
import Header from '../../components/Studies/Header';
import { Box, Divider, Typography } from '@mui/material';
import SideNav from '../../components/Studies/SideNav';
import StudiesList from '../../components/Studies/StudiesList';
import { GenericInfo, GroupDTO, StudyMetadata, UserDTO } from '../../common/types';
import { loadState, saveState } from '../../services/utils/localStorage';
import { convertVersions } from '../../services/utils';
import { getGroups, getUsers } from '../../services/api/user';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { getStudies } from '../../services/api/study';
import { connect, ConnectedProps } from 'react-redux';
import { AppState } from '../../store/reducers';
import { initStudies, initStudiesVersion } from '../../store/study';
import FilterDrawer from '../../components/Studies/FilterDrawer';

const DEFAULT_LIST_MODE_KEY = 'studylisting.listmode';
const DEFAULT_FILTER_USER = 'studylisting.filter.user';
const DEFAULT_FILTER_GROUP = 'studylisting.filter.group';
const DEFAULT_FILTER_VERSION = 'studylisting.filter.version';
const DEFAULT_FILTER_MANAGED = 'studylisting.filter.managed';
const DEFAULT_FILTER_SORTING = 'studylisting.filter.sorting';

interface SortElement {
    id: string;
    elm: string | (() => JSX.Element);
}

interface SortItem {
    element: SortElement;
    status: SortStatus;
}

type SortStatus = 'INCREASE' | 'DECREASE' | 'NONE';

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

function Studies(props: PropTypes) {
  const theme = useTheme();
  const { studies, loadStudies, loadVersions, versions } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [filteredStudies, setFilteredStudies] = useState<Array<StudyMetadata>>(studies);
  const [dirViewStudiesNb, setDirViewStudiesNb] = useState<number>(-1);
  const [loaded, setLoaded] = useState(true);
  const [managedFilter, setManageFilter] = useState(loadState<boolean>(DEFAULT_FILTER_MANAGED, false));
  const [currentSortItem, setCurrentSortItem] = useState<SortItem|undefined>(loadState<SortItem>(DEFAULT_FILTER_SORTING));
  const [ inputValue, setInputValue ] = useState<string>('');
  const [ openFilter, setOpenFiler ] = useState<boolean>(false);

  const onImportClick = () : void => {
    console.log('IMPORT');
  };

  const onCreateClick = () : void => {
    console.log('CREATE');
  }
  const onFilterClick = () : void => {
    console.log('FILTER');
    setOpenFiler(true);
  }


const getAllStudies = async (refresh: boolean) => {
  setLoaded(false);
  try {
    if (studies.length === 0 || refresh) {
      const allStudies = await getStudies();
      loadStudies(allStudies);
      setFilteredStudies(allStudies); // DELETE THIS
      console.log('YES SIR');
    }
  } catch (e) {
    //enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoretrievestudies'), e as AxiosError);
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

    console.log()
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
  saveState(DEFAULT_FILTER_USER, currentUser);
  saveState(DEFAULT_FILTER_GROUP, currentGroup);
  saveState(DEFAULT_FILTER_MANAGED, managedFilter);
  saveState(DEFAULT_FILTER_VERSION, currentVersion);
  saveState(DEFAULT_FILTER_SORTING, currentSortItem);
}, [currentVersion, currentUser, currentGroup, currentSortItem, managedFilter]);
  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
        <Header inputValue={inputValue} setInputValue={setInputValue} onImportClick={onImportClick} onCreateClick={onCreateClick} onFilterClick={onFilterClick} />
        <Divider style={{ width: '98%', background: theme.palette.grey[800] }}/>
        <Box flex={1} width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <SideNav />
          <Divider style={{ width: '1px', height: '98%', background: theme.palette.grey[800] }}/>
          <StudiesList studies={filteredStudies} />
          <FilterDrawer open={openFilter} />
        </Box>
     </Box>   
  );
}

export default connector(Studies);
