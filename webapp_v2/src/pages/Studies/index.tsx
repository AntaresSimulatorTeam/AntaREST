import React, { useEffect, useState } from 'react';
import { Box, Divider } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { connect, ConnectedProps } from 'react-redux';
import moment from 'moment';
import { AxiosError } from 'axios';
import Header from '../../components/Studies/Header';
import SideNav from '../../components/Studies/SideNav';
import StudiesList from '../../components/Studies/StudiesList';
import { GenericInfo, GroupDTO, StudyMetadata, UserDTO, SortElement, SortItem, SortStatus } from '../../common/types';
import { loadState, saveState } from '../../services/utils/localStorage';
import { convertVersions } from '../../services/utils';
import { getGroups, getUsers } from '../../services/api/user';
import { getStudies } from '../../services/api/study';
import { AppState } from '../../store/reducers';
import { initStudies, initStudiesVersion } from '../../store/study';
import FilterDrawer from '../../components/Studies/FilterDrawer';
import enqueueErrorSnackbar from '../../components/common/ErrorSnackBar';
import MainContentLoader from '../../components/common/loaders/MainContentLoader';

const DEFAULT_FILTER_USER = 'v2.studylisting.filter.user';
const DEFAULT_FILTER_GROUP = 'v2.studylisting.filter.group';
const DEFAULT_FILTER_VERSION = 'v2.studylisting.filter.version';
const DEFAULT_FILTER_MANAGED = 'v2.studylisting.filter.managed';
const DEFAULT_FILTER_SORTING = 'v2.studylisting.filter.sorting';
const DEFAULT_FILTER_FOLDER = 'v2.studylisting.filter.folder';
const DEFAULT_FAVORITE_STUDIES = 'v2.studylisting.favorite';

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
  const { studies, loadStudies, loadVersions, versions } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [filteredStudies, setFilteredStudies] = useState<Array<StudyMetadata>>(studies);
  const [loaded, setLoaded] = useState(true);
  const [managedFilter, setManageFilter] = useState(loadState<boolean>(DEFAULT_FILTER_MANAGED, false));
  const [currentSortItem, setCurrentSortItem] = useState<SortItem|undefined>(loadState<SortItem>(DEFAULT_FILTER_SORTING, { element: SortElement.NAME, status: SortStatus.INCREASE }));
  const [inputValue, setInputValue] = useState<string>('');
  const [openFilter, setOpenFiler] = useState<boolean>(false);

  const onFilterClick = () : void => {
    setOpenFiler(true);
  };
  const onFilterActionClick = (
    managed: boolean,
    versions: Array<GenericInfo> | undefined,
    users: Array<UserDTO> | undefined,
    groups: Array<GroupDTO> | undefined,
  ) : void => {
    setManageFilter(managed);
    setCurrentVersion(versions);
    setCurrentUser(users);
    setCurrentGroup(groups);
    setOpenFiler(false);
  };

  const getAllStudies = async (refresh: boolean) => {
    setLoaded(false);
    try {
      if (studies.length === 0 || refresh) {
        const allStudies = await getStudies();
        loadStudies(allStudies);
        setFilteredStudies(allStudies);
      }
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtoretrievestudies'), e as AxiosError);
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
  const [currentFolder, setCurrentFolder] = useState<string | undefined>(loadState<string>(DEFAULT_FILTER_FOLDER, 'root'));
  const [currentFavorite, setCurrentFavorite] = useState<Array<GenericInfo> | undefined>(loadState<Array<GenericInfo>>(DEFAULT_FAVORITE_STUDIES, []));

  const sortStudies = (): Array<StudyMetadata> => {
    const tmpStudies: Array<StudyMetadata> = ([] as Array<StudyMetadata>).concat(studies);
    if (currentSortItem) {
      tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
        const firstElm = currentSortItem.status === SortStatus.INCREASE ? studyA : studyB;
        const secondElm = currentSortItem.status === SortStatus.INCREASE ? studyB : studyA;
        if (currentSortItem.element === SortElement.NAME) {
          return firstElm.name.localeCompare(secondElm.name);
        }
        return (moment(firstElm.modificationDate).isAfter(moment(secondElm.modificationDate)) ? 1 : -1);
      });
    }
    return tmpStudies;
  };

  const insideFolder = (study: StudyMetadata) : boolean => {
    let studyNodeId = '';
    if (study.folder !== undefined && study.folder !== null) studyNodeId = `root/${study.workspace}/${study.folder}`;
    else studyNodeId = `root/${study.workspace}`;

    return studyNodeId.startsWith(currentFolder as string);
  };

  const filter = (currentName: string): StudyMetadata[] => sortStudies()
    .filter((s) => !currentName || (s.name.search(new RegExp(currentName, 'i')) !== -1) || (s.id.search(new RegExp(currentName, 'i')) !== -1))
    .filter((s) => !currentVersion || currentVersion.map((elm) => elm.id).includes(s.version))
    .filter((s) => (currentUser ? (s.owner.id && (currentUser as Array<UserDTO>).map((elm) => elm.id).includes(s.owner.id)) : true))
    .filter((s) => (currentGroup ? s.groups.findIndex((elm) => (currentGroup as Array<GroupDTO>).includes(elm)) >= 0 : true))
    .filter((s) => (managedFilter ? s.managed : true))
    .filter((s) => insideFolder(s));

  const applyFilter = () : void => {
    setLoaded(false);
    const f = filter(inputValue);
    setFilteredStudies(f);
    setLoaded(true);
  };

  const onChange = async (currentName: string) => {
    setLoaded(false);
    const f = filter(currentName);
    setFilteredStudies(f);
    setLoaded(true);
    if (currentName !== inputValue) setInputValue(currentName);
  };

  const handleFavoriteClick = (value: GenericInfo) => {
    const favorite = currentFavorite as Array<GenericInfo>;
    if (favorite.findIndex((elm) => (elm.id as string) === (value.id as string)) < 0) {
      setCurrentFavorite(favorite.concat(value));
      return;
    }
    setCurrentFavorite(favorite.filter((elm) => (elm.id as string) !== (value.id as string)));
  };

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
    if (!versions) {
      loadVersions();
    }
    getAllStudies(false);
  }, []);

  useEffect(() => {
    saveState(DEFAULT_FILTER_USER, currentUser);
    saveState(DEFAULT_FILTER_GROUP, currentGroup);
    saveState(DEFAULT_FILTER_MANAGED, managedFilter);
    saveState(DEFAULT_FILTER_VERSION, currentVersion);
    saveState(DEFAULT_FILTER_SORTING, currentSortItem);
    saveState(DEFAULT_FILTER_FOLDER, currentFolder);
    applyFilter();
  }, [currentVersion, currentUser, currentGroup, currentSortItem, managedFilter, currentFolder]);

  useEffect(() => {
    saveState(DEFAULT_FAVORITE_STUDIES, currentFavorite);
  }, [currentFavorite]);

  useEffect(() => {
    applyFilter();
  }, [studies]);

  return (
    <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" overflow="hidden">
      <Header managedFilter={managedFilter as boolean} setManageFilter={setManageFilter} inputValue={inputValue} setInputValue={onChange} onFilterClick={onFilterClick} />
      <Divider sx={{ width: '98%' }} />
      <Box flex={1} width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="flex-start" boxSizing="border-box">
        <SideNav studies={studies} folder={currentFolder as string} setFolder={setCurrentFolder} favorite={currentFavorite as Array<GenericInfo>} />
        <Divider sx={{ width: '1px', height: '98%', bgcolor: 'divider' }} />
        {!loaded && <MainContentLoader />}
        {loaded && studies && 
          <StudiesList studies={filteredStudies} 
                       sortItem={currentSortItem as SortItem} 
                       setSortItem={setCurrentSortItem} 
                       folder={currentFolder as string} 
                       setFolder={setCurrentFolder} 
                       favorite={currentFavorite !== undefined ? currentFavorite.map((elm) => elm.id as string) : []} 
                       onFavoriteClick={handleFavoriteClick} />}
        {openFilter && (
          <FilterDrawer
            open={openFilter}
            managedFilter={managedFilter as boolean}
            versionList={versionList}
            versions={currentVersion as Array<GenericInfo>}
            userList={userList}
            users={currentUser as Array<UserDTO>}
            groupList={groupList}
            groups={currentGroup as Array<GroupDTO>}
            onFilterActionClick={onFilterActionClick}
            onClose={() => setOpenFiler(false)}
          />
        )}
      </Box>
    </Box>
  );
}

export default connector(Studies);
