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
import moment from 'moment';

const DEFAULT_FILTER_USER = 'v2.studylisting.filter.user';
const DEFAULT_FILTER_GROUP = 'v2.studylisting.filter.group';
const DEFAULT_FILTER_VERSION = 'v2.studylisting.filter.version';
const DEFAULT_FILTER_MANAGED = 'v2.studylisting.filter.managed';
const DEFAULT_FILTER_SORTING = 'v2.studylisting.filter.sorting';

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
    console.log('OPEN FILTER');
    setOpenFiler(true);
  }
  const onFilterActionClick = (versions: Array<GenericInfo> | undefined,
                               users: Array<UserDTO> | undefined,
                               groups: Array<GroupDTO> | undefined) : void => {
    console.log('FILTER');
    setLoaded(true);
    setCurrentVersion(versions);
    setCurrentUser(users);
    setCurrentGroup(groups);
    const f = filter(inputValue);
    setFilteredStudies(f);
    setLoaded(false);
    setOpenFiler(false);
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

const versionList = convertVersions(versions || []);
const [userList, setUserList] = useState<Array<UserDTO>>([]);
const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
const [currentUser, setCurrentUser] = useState<Array<UserDTO>|undefined>(loadState<Array<UserDTO>>(DEFAULT_FILTER_USER));
const [currentGroup, setCurrentGroup] = useState<Array<GroupDTO>|undefined>(loadState<Array<GroupDTO>>(DEFAULT_FILTER_GROUP));
const [currentVersion, setCurrentVersion] = useState<Array<GenericInfo> | undefined>(loadState<Array<GenericInfo>>(DEFAULT_FILTER_VERSION));

const sortList = [ t('studymanager:sortByName'), t('studymanager:sortByDate') ];
const sortStudies = (): Array<StudyMetadata> => {
  const tmpStudies: Array<StudyMetadata> = ([] as Array<StudyMetadata>).concat(studies);
  if (currentSortItem && currentSortItem.status !== 'NONE') {
    tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
      const firstElm = currentSortItem.status === 'INCREASE' ? studyA : studyB;
      const secondElm = currentSortItem.status === 'INCREASE' ? studyB : studyA;
      if (currentSortItem.element.id === sortList[0]) {
        return firstElm.name.localeCompare(secondElm.name);
      }
      return (moment(firstElm.modificationDate).isAfter(moment(secondElm.modificationDate)) ? 1 : -1);
    });
  }
  return tmpStudies;
};


const filter = (currentName: string): StudyMetadata[] => sortStudies()
  .filter((s) => !currentName || (s.name.search(new RegExp(currentName, 'i')) !== -1) || (s.id.search(new RegExp(currentName, 'i')) !== -1))
  .filter((s) => !currentVersion || currentVersion.map((elm) => elm.id).includes(s.version))
  .filter((s) => (currentUser ? (s.owner.id && (currentUser as Array<UserDTO>).map((elm) => elm.id).includes(s.owner.id)) : true))
  .filter((s) => (currentGroup ? s.groups.findIndex((elm) => (currentGroup as Array<GroupDTO>).includes(elm)) >= 0 : true))
  .filter((s) => (managedFilter ? s.managed : true));

  const onChange = async (currentName: string) => {
    setLoaded(true);
    const f = filter(currentName);
    setFilteredStudies(f);
    setLoaded(false);
    if (currentName !== inputValue) setInputValue(currentName);
  };

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
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" overflow='hidden'>
        <Header inputValue={inputValue} setInputValue={onChange} onImportClick={onImportClick} onCreateClick={onCreateClick} onFilterClick={onFilterClick} />
        <Divider style={{ width: '98%', background: theme.palette.grey[800] }}/>
        <Box flex={1} width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <SideNav />
          <Divider style={{ width: '1px', height: '98%', background: theme.palette.grey[800] }}/>
          <StudiesList studies={filteredStudies} />
          {openFilter && <FilterDrawer open={openFilter}
                        managedFilter={managedFilter as boolean}
                        setManagedFilter={setManageFilter}
                        versionList={versionList}
                        versions={currentVersion as Array<GenericInfo>}
                        userList={userList}
                        users={currentUser as Array<UserDTO>}
                        groupList={groupList}
                        groups={currentGroup as Array<GroupDTO>}
                        onFilterActionClick={onFilterActionClick}
                        onClose={() => setOpenFiler(false)}/>}
        </Box>
     </Box>   
  );
}

export default connector(Studies);
