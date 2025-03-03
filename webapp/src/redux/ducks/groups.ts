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
import type { GroupDetailsDTO } from "../../types/types";
import { FetchStatus, makeActionName, type AsyncEntityState } from "../utils";
import * as api from "../../services/api/user";
import type { AppAsyncThunkConfig } from "../store";

const groupsAdapter = createEntityAdapter<GroupDetailsDTO>();

export type GroupsState = AsyncEntityState<GroupDetailsDTO>;

const initialState = groupsAdapter.getInitialState({
  status: FetchStatus.Idle,
  error: null as string | null,
}) as GroupsState;

const n = makeActionName("groups");

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const fetchGroups = createAsyncThunk<GroupDetailsDTO[], undefined, AppAsyncThunkConfig>(
  n("FETCH_GROUPS"),
  (_, { rejectWithValue }) => {
    return api.getGroups({ details: true }).catch(rejectWithValue);
  },
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(fetchGroups.pending, (draftState) => {
      draftState.status = FetchStatus.Loading;
    })
    .addCase(fetchGroups.fulfilled, (draftState, action) => {
      draftState.status = FetchStatus.Succeeded;
      groupsAdapter.removeAll(draftState);
      groupsAdapter.addMany(draftState, action);
    })
    .addCase(fetchGroups.rejected, (draftState, action) => {
      draftState.status = FetchStatus.Failed;
      draftState.error = action.error.message;
    });
});
