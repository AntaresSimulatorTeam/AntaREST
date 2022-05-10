import * as R from "ramda";
import { createSelector } from "reselect";
import { isGroupAdmin, isUserAdmin } from "../services/utils";
import { AppState } from "./ducks";
import { AuthState } from "./ducks/auth";
import { StudyState } from "./ducks/study";

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

export const getAuthUser = (state: AppState): AuthState["user"] =>
  state.auth.user;

export const isAuthUserAdmin = createSelector(getAuthUser, isUserAdmin);

export const isAuthUserInGroupAdmin = createSelector(getAuthUser, isGroupAdmin);

////////////////////////////////////////////////////////////////
// Studies
////////////////////////////////////////////////////////////////

export const getFavoriteStudies = (state: AppState): StudyState["favorites"] =>
  state.study.favorites;

export const getCurrentStudyId = (state: AppState): StudyState["current"] =>
  state.study.current;

export const isCurrentStudyFavorite = createSelector(
  getFavoriteStudies,
  getCurrentStudyId,
  (favorites, current) => !!R.find(R.propEq("id", current), favorites)
);
