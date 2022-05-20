import {
  createAction,
  ActionCreatorWithPayload,
  EntityState,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import { AppState } from "./ducks";
import { AppDispatch, AppThunk } from "./store";

const APP_NAME = "antarest";

export enum Status {
  Idle = "idle",
  Loading = "loading",
  Succeeded = "succeeded",
  Failed = "failed",
}

export interface AsyncEntityState<T> extends EntityState<T> {
  status: FetchStatus;
  error?: string;
}

export const makeActionName = R.curry(
  (reducerName: string, actionType: string) =>
    `${APP_NAME}/${reducerName}/${actionType}`
);

type ThunkAPI = { dispatch: AppDispatch; getState: () => AppState };

interface ThunkActionCreatorWithPayload<P, T = void>
  extends ActionCreatorWithPayload<P> {
  (thunkArg: T): AppThunk<P>;
}

export function createThunk<P = void, T = void>(
  typePrefix: string,
  payloadCreator: (arg: T, thunkAPI: ThunkAPI) => P
): ThunkActionCreatorWithPayload<P, T> {
  const actionCreator = createAction<T>(typePrefix);

  function thunkActionCreator(thunkArg: T): AppThunk<P> {
    return function thunkAction(dispatch, getState) {
      const payload = payloadCreator(thunkArg, { dispatch, getState });
      dispatch(actionCreator(payload));
      return payload;
    };
  }

  Object.assign(thunkActionCreator, actionCreator);

  return thunkActionCreator as ThunkActionCreatorWithPayload<P, T>;
}
