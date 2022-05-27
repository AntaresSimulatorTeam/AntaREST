import { createAsyncThunk, createReducer, isAnyOf } from "@reduxjs/toolkit";
import jwtDecode, { JwtPayload } from "jwt-decode";
import { UserInfo } from "../../common/types";
import * as authApi from "../../services/api/auth";
import * as clientApi from "../../services/api/client";
import { isUserExpired } from "../../services/utils";
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
  user: undefined,
} as AuthState;

const n = makeActionName("auth");

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const logout = createThunk(n("LOGOUT"), () => {
  clientApi.setAuth(null);
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

export const login = createAsyncThunk<
  UserInfo | undefined,
  LoginArg | UserInfo | undefined,
  AppAsyncThunkConfig
>(n("LOGIN"), async (arg, { dispatch, rejectWithValue }) => {
  let user;

  // Authentication not required or login from localStorage
  if (!arg || "id" in arg) {
    user = arg;
  }
  // Login from form
  else {
    try {
      const { username, password } = arg;
      const tokens = await authApi.login(username, password);
      const decoded = jwtDecode<JwtPayload>(tokens.access_token);
      const userData = JSON.parse(decoded.sub as string) as AccessTokenSub;

      clientApi.setAuth(tokens.access_token);

      user = {
        ...userData,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expirationDate: decoded.exp,
        user: username,
      } as UserInfo;
    } catch (err) {
      return rejectWithValue(err);
    }
  }

  initWebSocket(dispatch, user);
  clientApi.initAxiosInterceptors();

  return user;
});

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(logout, () => ({}))
    .addMatcher(
      isAnyOf(login.fulfilled, refresh.fulfilled),
      (draftState, action) => {
        draftState.user = action.payload;
      }
    );
});
