import * as R from "ramda";
import { createSelector } from "reselect";
import { StudyMetadata } from "../common/types";
import { isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { StudyState } from "./ducks/study";

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

export const getStudyState = (state: AppState): StudyState => state.study;

export const getStudies = (state: AppState): StudyState["studies"] => {
  return getStudyState(state).studies;
};

export const getStudy = (
  state: AppState,
  id: StudyMetadata["id"]
): StudyMetadata | undefined => {
  return getStudyState(state).studies.find((study) => study.id === id);
};

export const getFavoriteStudies = (
  state: AppState
): StudyState["favorites"] => {
  return getStudyState(state).favorites;
};

export const getStudyVersions = (
  state: AppState
): StudyState["versionList"] => {
  return getStudyState(state).versionList;
};

export const getCurrentStudyId = (state: AppState): StudyState["current"] => {
  return getStudyState(state).current;
};

export const getCurrentStudy = createSelector(
  getStudies,
  getCurrentStudyId,
  (studies, currentStudyId) => {
    return studies.find((study) => study.id === currentStudyId);
  }
);

export const isCurrentStudyFavorite = createSelector(
  getFavoriteStudies,
  getCurrentStudyId,
  (favorites, current) => !!R.find(R.propEq("id", current), favorites)
);
