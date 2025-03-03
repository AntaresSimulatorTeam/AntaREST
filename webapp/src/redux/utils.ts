/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { createAction, type ActionCreatorWithPayload, type EntityState } from "@reduxjs/toolkit";
import * as R from "ramda";
import type { AppState } from "./ducks";
import type { AppDispatch, AppThunk } from "./store";
import packages from "../../package.json";
import type { LinkElement } from "../types/types";

export enum FetchStatus {
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
  (reducerName: string, actionType: string) => `${packages.name}/${reducerName}/${actionType}`,
);

interface ThunkAPI {
  dispatch: AppDispatch;
  getState: () => AppState;
}

interface ThunkActionCreatorWithPayload<P, T = void> extends ActionCreatorWithPayload<P> {
  (thunkArg: T): AppThunk<P>;
}

export function createThunk<P = void, T = void>(
  typePrefix: string,
  payloadCreator: (arg: T, thunkAPI: ThunkAPI) => P,
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

const LINK_ID_SEPARATOR = " / ";

export function makeLinkId(sourceId: LinkElement["area1"], targetId: LinkElement["area2"]): string {
  return sourceId + LINK_ID_SEPARATOR + targetId;
}

export function parseLinkId(id: LinkElement["id"]): [string, string] {
  const [sourceId, targetId] = id.split(LINK_ID_SEPARATOR);
  return [sourceId, targetId];
}
