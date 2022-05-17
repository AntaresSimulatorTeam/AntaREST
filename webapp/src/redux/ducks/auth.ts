import {
  createAsyncThunk,
  createReducer,
  PayloadAction,
} from "@reduxjs/toolkit";
import jwtDecode, { JwtPayload } from "jwt-decode";
import * as RA from "ramda-adjunct";
import { AnyAction } from "redux";
import { UserInfo } from "../../common/types";
import * as authApi from "../../services/api/auth";
import * as clientApi from "../../services/api/client";
import { isUserExpired } from "../../services/utils";
import { loadState } from "../../services/utils/localStorage";
import {
  closeWebSocket,
  initWebSocket,
  reloadWebSocket,
} from "../../services/webSockets";
import { getAuthUser } from "../selectors";
import { AppAsyncThunkConfig } from "../store";
import { createThunk, makeActionName } from "../utils";

export interface AuthState {
  user?: UserInfo;
}

interface LoginArg {
  username: string;
  password: string;
}

type AccessTokenSub = Pick<UserInfo, "id" | "groups" | "impersonator" | "type">;

const initialState = {
  user: loadState("auth.user"),
} as AuthState;

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

const isActionWithUser = (
  action: AnyAction
): action is PayloadAction<UserInfo> => {
  return RA.isPlainObj(action.payload) ? "id" in action.payload : false;
};

const n = makeActionName("auth");

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const logout = createThunk(n("LOGOUT"), () => {
  clientApi.setAuth(undefined);
  closeWebSocket();
});

export const refresh = createAsyncThunk<
  UserInfo | undefined,
  void,
  AppAsyncThunkConfig
>(n("REFRESH"), async (_, { dispatch, getState, rejectWithValue }) => {
  const state = getState();
  const user = getAuthUser(state);

  if (user && isUserExpired(user)) {
    try {
      const tokens = await authApi.refresh(user.refreshToken);
      const decoded = jwtDecode<JwtPayload>(tokens.access_token);
      const newUserData = JSON.parse(decoded.sub as string) as AccessTokenSub;

      const userUpdated = {
        ...user,
        ...newUserData,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expirationDate: decoded.exp,
      };

      clientApi.setAuth(tokens.access_token);
      reloadWebSocket(dispatch, userUpdated);

      return userUpdated;
    } catch (err) {
      dispatch(logout());
      return rejectWithValue(err);
    }
  }

  return user;
});

export const login = createAsyncThunk<UserInfo, LoginArg, AppAsyncThunkConfig>(
  n("LOGIN"),
  async ({ username, password }, { dispatch, rejectWithValue }) => {
    try {
      const tokens = await authApi.login(username, password);
      const decoded = jwtDecode<JwtPayload>(tokens.access_token);
      const userData = JSON.parse(decoded.sub as string) as AccessTokenSub;

      clientApi.setAuth(tokens.access_token);

      const user = {
        ...userData,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expirationDate: decoded.exp,
        user: username,
      } as UserInfo;

      initWebSocket(dispatch, user);

      clientApi.setLogoutInterceptor(() => dispatch(logout()));
      clientApi.updateRefreshInterceptor(() => dispatch(refresh()).unwrap());

      return user;
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(logout, () => ({}))
    .addMatcher(isActionWithUser, (draftState, action) => {
      draftState.user = action.payload;
    });
});
