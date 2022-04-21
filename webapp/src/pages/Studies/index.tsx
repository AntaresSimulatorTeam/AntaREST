import { useCallback, useEffect, useState, memo, useRef } from "react";
import * as R from "ramda";
import { Box, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
import moment from "moment";
import { AxiosError } from "axios";
import debug from "debug";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { useMountedState } from "react-use";
import SideNav from "../../components/studies/SideNav";
import StudiesList, {
  StudyListProps,
} from "../../components/studies/StudiesList";
import {
  GenericInfo,
  GroupDTO,
  StudyMetadata,
  UserDTO,
  SortElement,
  SortItem,
  SortStatus,
  DefaultFilterKey,
} from "../../common/types";
import { loadState, saveState } from "../../services/utils/localStorage";
import { convertVersions } from "../../services/utils";
import { getGroups, getUsers } from "../../services/api/user";
import { getStudies } from "../../services/api/study";
import { AppState } from "../../store/reducers";
import { initStudies, initStudiesVersion } from "../../store/study";
import FilterDrawer from "../../components/studies/FilterDrawer";
import RootPage from "../../components/common/page/RootPage";
import HeaderTopRight from "../../components/studies/HeaderTopRight";
import HeaderBottom from "../../components/studies/HeaderBottom";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../../components/common/loaders/SimpleLoader";

const logErr = debug("antares:studies:error");

const StudiesListMemo = memo((props: StudyListProps) => (
  <StudiesList {...props} />
));

const mapState = (state: AppState) => ({
  studies: state.study.studies,
  versions: state.study.versionList,
});

const mapDispatch = {
  loadStudies: initStudies,
  loadVersions: initStudiesVersion,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function Studies(props: PropTypes) {
  const { studies, loadStudies, loadVersions, versions } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = useMountedState();
  const [filteredStudies, setFilteredStudies] =
    useState<Array<StudyMetadata>>(studies);
  const [loaded, setLoaded] = useState(false);
  const [managedFilter, setManageFilter] = useState(
    loadState<boolean>(DefaultFilterKey.MANAGED, false) || false
  );
  const [archivedFilter, setArchivedFilter] = useState(
    loadState<boolean>(DefaultFilterKey.ARCHIVED, false) || false
  );
  const [currentSortItem, setCurrentSortItem] = useState<SortItem | undefined>(
    loadState<SortItem>(DefaultFilterKey.SORTING, {
      element: SortElement.NAME,
      status: SortStatus.INCREASE,
    })
  );
  const [inputValue, setInputValue] = useState<string>("");
  const [openFilter, setOpenFiler] = useState<boolean>(false);
  const [userList, setUserList] = useState<Array<UserDTO>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [currentUser, setCurrentUser] = useState<Array<UserDTO> | undefined>(
    loadState<Array<UserDTO>>(DefaultFilterKey.USERS)
  );
  const [currentGroup, setCurrentGroup] = useState<Array<GroupDTO> | undefined>(
    loadState<Array<GroupDTO>>(DefaultFilterKey.GROUPS)
  );
  const [currentVersion, setCurrentVersion] = useState<
    Array<GenericInfo> | undefined
  >(loadState<Array<GenericInfo>>(DefaultFilterKey.VERSIONS));
  const [currentTag, setCurrentTag] = useState<Array<string> | undefined>(
    loadState<Array<string>>(DefaultFilterKey.TAGS)
  );
  const [currentFolder, setCurrentFolder] = useState<string | undefined>(
    loadState<string>(DefaultFilterKey.FOLDER, "root")
  );
  const [currentFavorite, setCurrentFavorite] = useState<Array<GenericInfo>>(
    loadState<Array<GenericInfo>>(DefaultFilterKey.FAVORITE_STUDIES, []) || []
  );

  // NOTE: GET TAG LIST FROM BACKEND
  const tagList: Array<string> = [];

  const onFilterClick = (): void => {
    setOpenFiler(true);
  };
  const onFilterActionClick = (
    managed: boolean,
    archived: boolean,
    versions: Array<GenericInfo> | undefined,
    users: Array<UserDTO> | undefined,
    groups: Array<GroupDTO> | undefined,
    tags: Array<string> | undefined
  ): void => {
    setManageFilter(managed);
    setArchivedFilter(archived);
    setCurrentVersion(versions);
    setCurrentUser(users);
    setCurrentGroup(groups);
    setCurrentTag(tags);
    setOpenFiler(false);
  };

  const getAllStudies = useCallback(
    async (refresh: boolean) => {
      setLoaded(false);
      try {
        if (studies.length === 0 || refresh) {
          const allStudies = await getStudies(false);
          loadStudies(allStudies);
          setFilteredStudies(allStudies);
        }
      } catch (e) {
        enqueueErrorSnackbar(
          t("studymanager:failtoretrievestudies"),
          e as AxiosError
        );
      } finally {
        setLoaded(true);
      }
    },
    [enqueueErrorSnackbar, loadStudies, studies.length, t]
  );

  const versionList = convertVersions(versions || []);

  const sortStudies = useCallback(
    (studyList: Array<StudyMetadata>): Array<StudyMetadata> => {
      const tmpStudies: Array<StudyMetadata> = (
        [] as Array<StudyMetadata>
      ).concat(studyList);
      if (currentSortItem) {
        tmpStudies.sort((studyA: StudyMetadata, studyB: StudyMetadata) => {
          const firstElm =
            currentSortItem.status === SortStatus.INCREASE ? studyA : studyB;
          const secondElm =
            currentSortItem.status === SortStatus.INCREASE ? studyB : studyA;
          if (currentSortItem.element === SortElement.NAME) {
            return firstElm.name.localeCompare(secondElm.name);
          }
          return moment(firstElm.modificationDate).isAfter(
            moment(secondElm.modificationDate)
          )
            ? 1
            : -1;
        });
      }
      return tmpStudies;
    },
    [currentSortItem]
  );

  const insideFolder = useCallback(
    (study: StudyMetadata): boolean => {
      let studyNodeId = "";
      if (study.folder !== undefined && study.folder !== null)
        studyNodeId = `root/${study.workspace}/${study.folder}`;
      else studyNodeId = `root/${study.workspace}`;

      return studyNodeId.startsWith(currentFolder as string);
    },
    [currentFolder]
  );

  const filterFromFolder = useCallback(
    (studyList: StudyMetadata[]) => {
      return studyList.filter((s) => insideFolder(s));
    },
    [insideFolder]
  );

  const filter = useCallback(
    (currentName: string): StudyMetadata[] =>
      sortStudies(filterFromFolder(studies))
        .filter(
          (s) =>
            !currentName ||
            s.name.search(new RegExp(currentName, "i")) !== -1 ||
            s.id.search(new RegExp(currentName, "i")) !== -1
        )
        .filter((s) =>
          currentTag && currentTag.length > 0
            ? s.tags &&
              s.tags.findIndex((elm) =>
                (currentTag as Array<string>).includes(elm)
              ) >= 0
            : true
        )
        .filter(
          (s) =>
            !currentVersion ||
            currentVersion.map((elm) => elm.id).includes(s.version)
        )
        .filter((s) =>
          currentUser
            ? s.owner.id &&
              (currentUser as Array<UserDTO>)
                .map((elm) => elm.id)
                .includes(s.owner.id)
            : true
        )
        .filter((s) =>
          currentGroup
            ? R.intersection(
                s.groups.map(R.prop("id")),
                currentGroup.map(R.prop("id"))
              ).length > 0
            : true
        )
        .filter((s) => (managedFilter ? s.managed : true))
        .filter((s) => (archivedFilter ? s.archived : true)),
    [
      currentVersion,
      currentUser,
      currentGroup,
      currentTag,
      managedFilter,
      archivedFilter,
      filterFromFolder,
      sortStudies,
      studies,
    ]
  );

  const filterActionTimeout = useRef<NodeJS.Timeout>();

  const applyFilter = useCallback((): void => {
    setLoaded(false);
    if (filterActionTimeout.current) {
      clearTimeout(filterActionTimeout.current);
    }
    filterActionTimeout.current = setTimeout(() => {
      if (mounted()) {
        const f = filter(inputValue);
        setFilteredStudies(f);
        setLoaded(true);
      }
    }, 0);
  }, [filter, inputValue, mounted]);

  const handleFavoriteClick = useCallback(
    (value: GenericInfo) => {
      const favorite = currentFavorite as Array<GenericInfo>;
      if (
        favorite.findIndex(
          (elm) => (elm.id as string) === (value.id as string)
        ) < 0
      ) {
        setCurrentFavorite(favorite.concat(value));
        return;
      }
      setCurrentFavorite(
        favorite.filter((elm) => (elm.id as string) !== (value.id as string))
      );
    },
    [currentFavorite]
  );

  const init = async () => {
    try {
      const userRes = await getUsers();
      setUserList(userRes);

      const groupRes = await getGroups();
      setGroupList(groupRes);
    } catch (error) {
      logErr(error);
    }
  };

  useEffect(() => {
    init();
    if (!versions) {
      loadVersions();
    }
    getAllStudies(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    saveState(DefaultFilterKey.USERS, currentUser);
    saveState(DefaultFilterKey.GROUPS, currentGroup);
    saveState(DefaultFilterKey.MANAGED, managedFilter);
    saveState(DefaultFilterKey.ARCHIVED, archivedFilter);
    saveState(DefaultFilterKey.VERSIONS, currentVersion);
    saveState(DefaultFilterKey.TAGS, currentTag);
    saveState(DefaultFilterKey.SORTING, currentSortItem);
    saveState(DefaultFilterKey.FOLDER, currentFolder);
    applyFilter();
  }, [
    currentVersion,
    currentUser,
    currentGroup,
    currentTag,
    currentSortItem,
    managedFilter,
    archivedFilter,
    currentFolder,
    applyFilter,
  ]);

  useEffect(() => {
    saveState(DefaultFilterKey.FAVORITE_STUDIES, currentFavorite);
  }, [currentFavorite]);

  useEffect(() => {
    setCurrentFavorite((prev) => {
      if (prev && prev.length > 0 && studies.length > 0) {
        const studyIds = studies.map((item) => item.id);
        return prev.filter((elm) => studyIds.includes(elm.id as string));
      }
      return prev;
    });
    applyFilter();
  }, [applyFilter, setCurrentFavorite, studies]);

  const refreshStudies = useCallback(
    () => getAllStudies(true),
    [getAllStudies]
  );

  return (
    <RootPage
      title={t("main:studies")}
      titleIcon={TravelExploreOutlinedIcon}
      headerTopRight={<HeaderTopRight />}
      headerBottom={
        <HeaderBottom
          {...{
            inputValue,
            setInputValue: (newValue) => {
              if (newValue !== inputValue) setInputValue(newValue);
            },
            onFilterClick,
            managedFilter,
            setManageFilter,
            archivedFilter,
            setArchivedFilter,
            versions: currentVersion,
            setVersions: setCurrentVersion,
            users: currentUser,
            setUsers: setCurrentUser,
            groups: currentGroup,
            setGroups: setCurrentGroup,
            tags: currentTag,
            setTags: setCurrentTag,
          }}
        />
      }
    >
      <Box
        flex={1}
        width="100%"
        display="flex"
        flexDirection="row"
        justifyContent="flex-start"
        alignItems="flex-start"
        boxSizing="border-box"
      >
        <SideNav
          studies={studies}
          folder={currentFolder as string}
          setFolder={setCurrentFolder}
          favorite={currentFavorite as Array<GenericInfo>}
        />
        <Divider sx={{ width: "1px", height: "98%", bgcolor: "divider" }} />
        {!loaded && <SimpleLoader />}
        {loaded && studies && (
          <StudiesListMemo
            refresh={refreshStudies}
            studies={filteredStudies}
            sortItem={currentSortItem as SortItem}
            setSortItem={setCurrentSortItem}
            folder={currentFolder as string}
            setFolder={setCurrentFolder}
            favorites={currentFavorite}
            onFavoriteClick={handleFavoriteClick}
          />
        )}
        <FilterDrawer
          open={openFilter}
          managedFilter={managedFilter as boolean}
          archivedFilter={archivedFilter as boolean}
          tagList={tagList}
          tags={currentTag as Array<string>}
          versionList={versionList}
          versions={currentVersion as Array<GenericInfo>}
          userList={userList}
          users={currentUser as Array<UserDTO>}
          groupList={groupList}
          groups={currentGroup as Array<GroupDTO>}
          onFilterActionClick={onFilterActionClick}
          onClose={() => setOpenFiler(false)}
        />
      </Box>
    </RootPage>
  );
}

export default connector(Studies);
