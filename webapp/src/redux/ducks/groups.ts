import {
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import { GroupDetailsDTO } from "../../common/types";
import { AsyncEntityState, FetchStatus, makeActionName } from "../utils";
import * as api from "../../services/api/user";
import { AppAsyncThunkConfig } from "../store";

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

export const fetchGroups = createAsyncThunk<
  GroupDetailsDTO[],
  undefined,
  AppAsyncThunkConfig
>(n("FETCH_GROUPS"), (_, { rejectWithValue }) => {
  return api.getGroups({ details: true }).catch(rejectWithValue);
});

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
