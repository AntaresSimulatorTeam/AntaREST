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

import { createAsyncThunk, createEntityAdapter, createReducer } from "@reduxjs/toolkit";
import type { UserDetailsDTO } from "../../types/types";
import { FetchStatus, makeActionName, type AsyncEntityState } from "../utils";
import * as api from "../../services/api/user";
import type { AppAsyncThunkConfig } from "../store";

const usersAdapter = createEntityAdapter<UserDetailsDTO>();

export type UsersState = AsyncEntityState<UserDetailsDTO>;

const initialState = usersAdapter.getInitialState({
  status: FetchStatus.Idle,
  error: null as string | null,
}) as UsersState;

const n = makeActionName("users");

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const fetchUsers = createAsyncThunk<UserDetailsDTO[], undefined, AppAsyncThunkConfig>(
  n("FETCH_USERS"),
  (_, { rejectWithValue }) => {
    return api.getUsers({ details: true }).catch(rejectWithValue);
  },
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(fetchUsers.pending, (draftState) => {
      draftState.status = FetchStatus.Loading;
    })
    .addCase(fetchUsers.fulfilled, (draftState, action) => {
      draftState.status = FetchStatus.Succeeded;
      usersAdapter.removeAll(draftState);
      usersAdapter.addMany(draftState, action);
    })
    .addCase(fetchUsers.rejected, (draftState, action) => {
      draftState.status = FetchStatus.Failed;
      draftState.error = action.error.message;
    });
});
