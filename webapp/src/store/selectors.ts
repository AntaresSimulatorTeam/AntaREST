import { createSelector } from "reselect";
import { isGroupAdmin, isUserAdmin } from "../services/utils";
import { AuthState } from "./auth";
import { AppState } from "./reducers";

////////////////////////////////////////////////////////////////
// Auth
////////////////////////////////////////////////////////////////

export const getAuthUser = (state: AppState): AuthState["user"] =>
  state.auth.user;

export const isAuthUserAdmin = createSelector(getAuthUser, isUserAdmin);

export const isAuthUserInGroupAdmin = createSelector(getAuthUser, isGroupAdmin);
