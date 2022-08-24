import { createEntityAdapter, createSelector } from "@reduxjs/toolkit";
import {
  Cluster,
  FileStudyTreeConfigDTO,
  GroupDetailsDTO,
  LinkListElement,
  StudyMetadata,
  UserDetailsDTO,
} from "../common/types";
import { buildStudyTree } from "../components/App/Studies/utils";
import { filterStudies, sortStudies } from "../utils/studiesUtils";
import { convertVersions, isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { GroupsState } from "./ducks/groups";
import { StudiesSortConf, StudiesState, StudyFilters } from "./ducks/studies";
import { studyDataAdapter, StudyDataState } from "./ducks/studyDataSynthesis";
import { UIState } from "./ducks/ui";
import { UsersState } from "./ducks/users";

// TODO resultEqualityCheck

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

export const getAuthUser = (state: AppState): AuthState["user"] => {
  return state.auth.user;
};

export const isAuthUserAdmin = createSelector(getAuthUser, isUserAdmin);

export const isAuthUserInGroupAdmin = createSelector(getAuthUser, isGroupAdmin);

////////////////////////////////////////////////////////////////
// Study
////////////////////////////////////////////////////////////////

export const getStudiesState = (state: AppState): StudiesState => state.studies;

export const getStudiesStatus = (state: AppState): StudiesState["status"] => {
  return getStudiesState(state).status;
};

export const getStudiesScrollPosition = (
  state: AppState
): StudiesState["scrollPosition"] => {
  return getStudiesState(state).scrollPosition;
};

const studiesSelectors =
  createEntityAdapter<StudyMetadata>().getSelectors(getStudiesState);

export const getStudies = studiesSelectors.selectAll;

export const getStudiesById = studiesSelectors.selectEntities;

export const getStudyIds = studiesSelectors.selectIds;

export const getStudy = studiesSelectors.selectById;

export const getFavoriteStudyIds = (
  state: AppState
): StudiesState["favorites"] => {
  return getStudiesState(state).favorites;
};

export const getFavoriteStudies = createSelector(
  getStudiesById,
  getFavoriteStudyIds,
  (studiesById, favoriteIds) => {
    return favoriteIds
      .map((favId) => studiesById[favId])
      .filter((item): item is StudyMetadata => !!item);
  }
);

export const isStudyFavorite = (
  state: AppState,
  id: StudyMetadata["id"]
): boolean => {
  return getFavoriteStudyIds(state).includes(id);
};

export const getStudyFilters = (state: AppState): StudyFilters => {
  return getStudiesState(state).filters;
};

export const getStudiesSortConf = (state: AppState): StudiesSortConf => {
  return getStudiesState(state).sort;
};

export const getStudiesFilteredAndSorted = createSelector(
  getStudies,
  getStudyFilters,
  getStudiesSortConf,
  (studies, filters, sortConf) => {
    const sorted = sortStudies(sortConf, studies);
    return filterStudies(filters, sorted);
  }
);

export const getStudyIdsFilteredAndSorted = createSelector(
  getStudiesFilteredAndSorted,
  (studies) => studies.map((study) => study.id)
);

export const getStudiesTree = createSelector(getStudies, buildStudyTree);

export const getStudyVersions = (
  state: AppState
): StudiesState["versionList"] => {
  return getStudiesState(state).versionList;
};

export const getStudyVersionsFormatted = createSelector(
  getStudyVersions,
  convertVersions
);

export const getCurrentStudyId = (state: AppState): StudiesState["current"] => {
  return getStudiesState(state).current;
};

export const getCurrentStudy = createSelector(
  studiesSelectors.selectEntities,
  getCurrentStudyId,
  (studies, current) => studies[current]
);

export const isCurrentStudyFavorite = createSelector(
  getFavoriteStudyIds,
  getCurrentStudyId,
  (favorites, current) => favorites.includes(current)
);

////////////////////////////////////////////////////////////////
// Users
////////////////////////////////////////////////////////////////

const getUsersState = (state: AppState): UsersState => state.users;

const usersSelectors =
  createEntityAdapter<UserDetailsDTO>().getSelectors(getUsersState);

export const getUsers = usersSelectors.selectAll;

export const getUsersById = usersSelectors.selectEntities;

export const getUserIds = usersSelectors.selectIds;

export const getUser = usersSelectors.selectById;

////////////////////////////////////////////////////////////////
// Groups
////////////////////////////////////////////////////////////////

const getGroupsState = (state: AppState): GroupsState => state.groups;

const groupsSelectors =
  createEntityAdapter<GroupDetailsDTO>().getSelectors(getGroupsState);

export const getGroups = groupsSelectors.selectAll;

export const getGroupsById = groupsSelectors.selectEntities;

export const getGroupIds = groupsSelectors.selectIds;

export const getGroup = groupsSelectors.selectById;

////////////////////////////////////////////////////////////////
// Study Data Synthesis
////////////////////////////////////////////////////////////////

export const getStudyDataState = (state: AppState): StudyDataState =>
  state.studyDataSynthesis;

const studyDataSelectors = studyDataAdapter.getSelectors(getStudyDataState);

export const getStudyDataIds = studyDataSelectors.selectIds;

export const getAllStudyData = studyDataSelectors.selectAll;

export const getStudyData = studyDataSelectors.selectById;

export const getCurrentAreaId = (
  state: AppState
): StudyDataState["currentArea"] => {
  return getStudyDataState(state).currentArea;
};

export const getCurrentLinkId = (
  state: AppState
): StudyDataState["currentLink"] => {
  return getStudyDataState(state).currentLink;
};

export const getStudyAreas = createSelector(getStudyData, (studyData) =>
  studyData ? Object.values(studyData.areas) : []
);

export const selectLinks = (
  studyData: FileStudyTreeConfigDTO | undefined
): LinkListElement | undefined => {
  if (studyData) {
    const links: LinkListElement = {};
    Object.keys(studyData.areas).forEach((elm1) => {
      const area1 = studyData.areas[elm1];
      Object.keys(area1.links).forEach((elm2) => {
        const area2 = studyData.areas[elm2];
        const area1Id = elm1.localeCompare(elm2) < 0 ? elm1 : elm2;
        const area2Id = elm1 === area1Id ? elm2 : elm1;
        const name = `${area1Id} / ${area2Id}`;
        links[name] = {
          label: `${area1.name} / ${area2.name}`,
          name,
          area1: area1Id,
          area2: area2Id,
        };
      });
    });
    return links;
  }
  return undefined;
};

export const getStudyLinks = createSelector(getStudyData, (data) => {
  if (data) {
    const tmp = selectLinks(data);
    if (tmp) return Object.values(tmp) || [];
  }
  return [];
});

export const getCurrentBindingConstId = (
  state: AppState
): StudyDataState["currentBindingConst"] => {
  return getStudyDataState(state).currentBindingConst;
};

export const getCurrentClusters = (
  type: "thermals" | "renewables",
  studyId: string,
  state: AppState
): Array<Cluster> => {
  const currentStudyState = getStudyDataState(state);
  const { currentArea } = currentStudyState;
  const clusters =
    currentStudyState.entities[studyId]?.areas[currentArea][type];
  return clusters || [];
};

export const getBindingConst = createSelector(getStudyData, (studyData) =>
  studyData ? studyData.bindings || [] : []
);

////////////////////////////////////////////////////////////////
// UI
////////////////////////////////////////////////////////////////

const getUIState = (state: AppState): AppState["ui"] => state.ui;

export const getWebSocketConnected = (
  state: AppState
): UIState["webSocketConnected"] => {
  return getUIState(state).webSocketConnected;
};

export const getTaskNotificationsCount = (
  state: AppState
): UIState["taskNotificationsCount"] => {
  return getUIState(state).taskNotificationsCount;
};

export const getMaintenanceMode = (
  state: AppState
): UIState["maintenanceMode"] => {
  return getUIState(state).maintenanceMode;
};

export const getMessageInfo = (state: AppState): UIState["messageInfo"] => {
  return getUIState(state).messageInfo;
};

export const getMenuExtended = (state: AppState): UIState["menuExtended"] => {
  return getUIState(state).menuExtended;
};
