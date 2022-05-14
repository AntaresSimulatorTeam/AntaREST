import * as R from "ramda";
import { createSelector } from "reselect";
import { isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { studiesAdapter, StudiesState } from "./ducks/studies";

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

const studiesSelectors = studiesAdapter.getSelectors(getStudiesState);

export const getStudies = studiesSelectors.selectAll;

export const getStudy = studiesSelectors.selectById;

export const getFavoriteStudies = (
  state: AppState
): StudiesState["favorites"] => {
  return getStudiesState(state).favorites;
};

export const getStudyVersions = (
  state: AppState
): StudiesState["versionList"] => {
  return getStudiesState(state).versionList;
};

export const getCurrentStudyId = (state: AppState): StudiesState["current"] => {
  return getStudiesState(state).current;
};

export const getCurrentStudy = createSelector(
  studiesSelectors.selectEntities,
  getCurrentStudyId,
  (studies, currentStudyId) => {
    return currentStudyId ? studies[currentStudyId] : null;
  }
);

export const isCurrentStudyFavorite = createSelector(
  getFavoriteStudies,
  getCurrentStudyId,
  (favorites, current) => !!R.find(R.propEq("id", current), favorites)
);
