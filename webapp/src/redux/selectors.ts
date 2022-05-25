import { createEntityAdapter, createSelector } from "@reduxjs/toolkit";
import { StudyMetadata } from "../common/types";
import { buildStudyTree } from "../components/studies/utils";
import { filterStudies, sortStudies } from "../pages/Studies/utils";
import { convertVersions, isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { StudiesSortConf, StudiesState, StudyFilters } from "./ducks/studies";
import { UIState } from "./ducks/ui";

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
