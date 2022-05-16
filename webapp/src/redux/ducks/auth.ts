import {
  createAsyncThunk,
  createReducer,
  PayloadAction,
} from "@reduxjs/toolkit";
import jwtDecode, { JwtPayload } from "jwt-decode";
import moment, { Moment } from "moment";
import * as RA from "ramda-adjunct";
import { AnyAction } from "redux";
import { UserInfo } from "../../common/types";
import * as authApi from "../../services/api/auth";
import * as clientApi from "../../services/api/client";
import { loadState } from "../../services/utils/localStorage";
import { getAuthUser } from "../selectors";
import { AppAsyncThunkConfig } from "../store";
import { createThunk, makeActionName } from "../utils";
import { reconnectWebsocket } from "./websockets";

export interface AuthState {
  user?: UserInfo;
}

interface LoginArg {
  username: string;
  password: string;
}

interface RefreshArg {
  logoutOnError: boolean;
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

const makeExpirationDate = (payload: JwtPayload): Moment | undefined => {
  return payload.exp ? moment.unix(payload.exp) : undefined;
};

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

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
        expirationDate: makeExpirationDate(decoded),
        user: username,
      } as UserInfo;

      dispatch(reconnectWebsocket(user));

      return user;
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

export const logout = createThunk(n("LOGOUT"), () => {
  clientApi.setAuth(undefined);
});

export const refresh = createAsyncThunk<
  UserInfo | undefined,
  RefreshArg | undefined,
  AppAsyncThunkConfig
>(n("REFRESH"), async (arg, { dispatch, getState, rejectWithValue }) => {
  const state = getState();
  const user = getAuthUser(state);

  if (
    user &&
    (!user.expirationDate || user.expirationDate < moment().add(5, "s"))
  ) {
    try {
      const tokens = await authApi.refresh(user.refreshToken);
      const decoded = jwtDecode<JwtPayload>(tokens.access_token);
      const newUserData = JSON.parse(decoded.sub as string) as AccessTokenSub;

      clientApi.setAuth(tokens.access_token);

      return {
        ...user,
        ...newUserData,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expirationDate: makeExpirationDate(decoded),
      };
    } catch (err) {
      if (arg?.logoutOnError) {
        dispatch(logout());
      }
      return rejectWithValue(err);
    }
  }

  return user;
});

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
