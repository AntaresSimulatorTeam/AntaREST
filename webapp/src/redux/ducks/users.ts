import {
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import { UserDetailsDTO } from "../../common/types";
import { AsyncEntityState, FetchStatus, makeActionName } from "../utils";
import * as api from "../../services/api/user";
import { AppAsyncThunkConfig } from "../store";

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

export const fetchUsers = createAsyncThunk<
  UserDetailsDTO[],
  undefined,
  AppAsyncThunkConfig
>(n("FETCH_USERS"), (_, { rejectWithValue }) => {
  return api.getUsers({ details: true }).catch(rejectWithValue);
});

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
