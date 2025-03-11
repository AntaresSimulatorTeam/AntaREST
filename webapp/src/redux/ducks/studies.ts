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

import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import type { O } from "ts-toolbelt";
import type { GroupDTO, StudyMetadata, StudyPublicMode, UserDTO } from "../../types/types";
import * as api from "../../services/api/study";
import { getFavoriteStudyIds, getStudyVersions } from "../selectors";
import type { AppAsyncThunkConfig, AppThunk } from "../store";
import { makeActionName, FetchStatus, createThunk, type AsyncEntityState } from "../utils";
import { setDefaultAreaLinkSelection } from "./studySyntheses";
import type { StudyEventPayload } from "@/services/webSocket/types";

const studiesAdapter = createEntityAdapter<StudyMetadata>();

export interface StudyFilters {
  inputValue: string;
  folder: string;
  strictFolder: boolean;
  managed: boolean;
  archived: boolean;
  variant: boolean;
  versions: string[];
  users: Array<UserDTO["id"]>;
  groups: Array<GroupDTO["id"]>;
  tags: string[];
}

export interface StudiesSortConf {
  property: keyof StudyMetadata;
  order: "ascend" | "descend";
}

export interface StudiesState extends AsyncEntityState<StudyMetadata> {
  current: string;
  prevStudyId: string;
  scrollPosition: number;
  versionList: string[];
  favorites: Array<StudyMetadata["id"]>;
  filters: StudyFilters;
  sort: StudiesSortConf;
}

interface StudyCreator {
  name: string;
  version?: string;
  groups?: string[];
  publicMode?: StudyPublicMode;
  tags?: string[];
}

interface StudyUpload {
  file: File;
  onUploadProgress?: (progress: number) => void;
}

type CreateStudyArg = StudyCreator | StudyUpload | StudyMetadata;

const initialState = studiesAdapter.getInitialState({
  status: FetchStatus.Idle,
  error: null as string | null,
  current: "",
  prevStudyId: "",
  scrollPosition: 0,
  versionList: [] as string[],
  favorites: [],
  filters: {
    inputValue: "",
    folder: "root",
    strictFolder: false,
    managed: false,
    archived: false,
    variant: false,
    versions: [],
    users: [],
    groups: [],
    tags: [],
  },
  sort: {
    property: "name",
    order: "ascend",
  },
}) as StudiesState;

const n = makeActionName("study");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentStudy = createThunk<
  NonNullable<StudiesState["current"]>,
  NonNullable<StudiesState["current"]>
>(n("SET_CURRENT"), (arg: string, { dispatch }) => {
  dispatch(setDefaultAreaLinkSelection(arg));
  return arg;
});

export const setStudyScrollPosition = createAction<StudiesState["scrollPosition"]>(
  n("SET_SCROLL_POSITION"),
);

export const setFavoriteStudies = createAction<StudiesState["favorites"]>(n("SET_FAVORITES"));

export const updateStudyFilters = createAction<Partial<StudiesState["filters"]>>(
  n("UPDATE_FILTERS"),
);

export const updateStudiesSortConf = createAction<Partial<StudiesState["sort"]>>(
  n("UPDATE_SORT_CONF"),
);

export const updateStudiesFromLocalStorage = createAction<
  O.Nullable<{
    favorites: StudiesState["favorites"];
    sort: Partial<StudiesSortConf>;
  }>
>(n("UPDATE_FROM_LOCAL_STORAGE"));

export const updateStudy = createAction<{
  id: StudyMetadata["id"];
  changes: Partial<Omit<StudyMetadata, "id">>;
}>(n("UPDATE_STUDY"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createStudy = createAsyncThunk<StudyMetadata, CreateStudyArg, AppAsyncThunkConfig>(
  n("CREATE_STUDY"),
  async (arg, { getState, rejectWithValue }) => {
    // StudyMetadata
    if ("id" in arg) {
      return arg;
    }

    try {
      // StudyUpload
      if ("file" in arg) {
        const { file, onUploadProgress } = arg;
        const studyId = await api.importStudy(file, onUploadProgress);
        return api.getStudyMetadata(studyId);
      }

      // StudyCreator
      const { name, version, groups, publicMode, tags } = arg;
      const state = getState();
      const versionList = getStudyVersions(state) || [];
      const studyVersion = Number(version || R.last(versionList));
      // TODO: add publicMode and tags in createStudy API to prevent multiple WebSocket trigger
      const studyId = await api.createStudy(name, studyVersion, groups);
      if (publicMode) {
        await api.changePublicMode(studyId, publicMode);
      }
      if (tags && tags.length > 0) {
        await api.updateStudyMetadata(studyId, { tags });
      }
      return api.getStudyMetadata(studyId);
    } catch (err) {
      return rejectWithValue(err);
    }
  },
);

export const setStudy = createAsyncThunk<StudyMetadata, StudyEventPayload, AppAsyncThunkConfig>(
  n("SET_STUDY"),
  ({ id }) => api.getStudyMetadata(id),
);

interface StudyDeleteInfo {
  id: StudyMetadata["id"];
  deleteChildren?: boolean;
}

export const deleteStudy = createAsyncThunk<
  StudyMetadata["id"],
  StudyDeleteInfo | StudyEventPayload,
  AppAsyncThunkConfig
>(n("DELETE_STUDY"), async (arg, { dispatch, getState, rejectWithValue }) => {
  let studyId: string;
  // WebSocket
  if ("name" in arg) {
    studyId = arg.id;
  } else {
    const { id, deleteChildren } = arg;
    studyId = id;
    try {
      await api.deleteStudy(studyId, deleteChildren);
    } catch (err) {
      return rejectWithValue(err);
    }
  }

  const state = getState();
  const currentFavorites = getFavoriteStudyIds(state);
  const newFavorites = currentFavorites.filter((fav) => fav !== studyId);
  dispatch(setFavoriteStudies(newFavorites));

  return studyId;
});

export const fetchStudyVersions = createAsyncThunk(
  n("FETCH_VERSIONS"),
  (_, { rejectWithValue }) => {
    return api.getStudyVersions().catch(rejectWithValue);
  },
);

export const fetchStudies = createAsyncThunk<StudyMetadata[], undefined, AppAsyncThunkConfig>(
  n("FETCH_STUDIES"),
  async (_, { dispatch, getState, rejectWithValue }) => {
    try {
      const studies = await api.getStudies();
      dispatch(fetchStudyVersions());

      return studies;
    } catch (err) {
      return rejectWithValue(err);
    }
  },
);

export const toggleFavorite =
  (studyId: StudyMetadata["id"]): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    const currentFavorites = getFavoriteStudyIds(state);
    const isFav = !!currentFavorites.find((fav) => fav === studyId);

    dispatch(
      setFavoriteStudies(
        isFav ? currentFavorites.filter((fav) => fav !== studyId) : [...currentFavorites, studyId],
      ),
    );
  };

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(updateStudiesFromLocalStorage, (draftState, action) => {
      const { favorites, sort } = action.payload;
      draftState.favorites = favorites || [];
      Object.assign(draftState.sort, sort);
    })
    .addCase(createStudy.fulfilled, studiesAdapter.addOne)
    .addCase(setStudy.fulfilled, studiesAdapter.setOne)
    .addCase(updateStudy, studiesAdapter.updateOne)
    .addCase(deleteStudy.fulfilled, studiesAdapter.removeOne)
    .addCase(fetchStudies.pending, (draftState) => {
      draftState.status = FetchStatus.Loading;
    })
    .addCase(fetchStudies.fulfilled, (draftState, action) => {
      draftState.status = FetchStatus.Succeeded;
      studiesAdapter.removeAll(draftState);
      studiesAdapter.addMany(draftState, action);
    })
    .addCase(fetchStudies.rejected, (draftState, action) => {
      draftState.status = FetchStatus.Failed;
      draftState.error = action.error.message;
    })
    .addCase(setFavoriteStudies, (draftState, action) => {
      draftState.favorites = action.payload;
    })
    .addCase(updateStudyFilters, (draftState, action) => {
      Object.assign(draftState.filters, action.payload);
      draftState.scrollPosition = 0;
    })
    .addCase(updateStudiesSortConf, (draftState, action) => {
      Object.assign(draftState.sort, action.payload);
      draftState.scrollPosition = 0;
    })
    .addCase(fetchStudyVersions.fulfilled, (draftState, action) => {
      draftState.versionList = action.payload;
    })
    .addCase(setCurrentStudy, (draftState, action) => {
      draftState.prevStudyId = draftState.current;
      draftState.current = action.payload;
    })
    .addCase(setStudyScrollPosition, (draftState, action) => {
      draftState.scrollPosition = action.payload;
    });
});
