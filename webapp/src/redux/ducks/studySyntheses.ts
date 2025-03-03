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
import type {
  FileStudyTreeConfigDTO,
  GenericInfo,
  LaunchJobDTO,
  Link,
  LinkElement,
} from "../../types/types";
import * as api from "../../services/api/study";
import { getStudyMapsIds, getStudySynthesis, getStudySynthesisIds } from "../selectors";
import type { AppAsyncThunkConfig, AppDispatch, AppThunk } from "../store";
import { makeActionName } from "../utils";
import { setStudyMap } from "./studyMaps";

export const studySynthesesAdapter = createEntityAdapter<FileStudyTreeConfigDTO>({
  selectId: (studyData) => studyData.study_id,
});

export interface StudySynthesesState
  extends ReturnType<typeof studySynthesesAdapter.getInitialState> {
  currentArea: string;
  currentLink: string;
  currentBindingConst: string;
}

const initialState = studySynthesesAdapter.getInitialState({
  currentArea: "",
  currentLink: "",
  currentBindingConst: "",
}) as StudySynthesesState;

const n = makeActionName("studySyntheses");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentArea = createAction<NonNullable<StudySynthesesState["currentArea"]>>(
  n("SET_CURRENT_AREA"),
);

export const setCurrentLink = createAction<NonNullable<StudySynthesesState["currentLink"]>>(
  n("SET_CURRENT_LINK"),
);

export const setCurrentBindingConst = createAction<
  NonNullable<StudySynthesesState["currentBindingConst"]>
>(n("SET_CURRENT_BINDING_CONST"));

export const updateStudySynthesis = createAction<{
  id: FileStudyTreeConfigDTO["study_id"];
  changes: Partial<Omit<FileStudyTreeConfigDTO, "study_id">>;
}>(n("UPDATE_STUDY_SYNTHESIS"));

export const createStudyLink = createAction<{
  studyId: FileStudyTreeConfigDTO["study_id"];
  area1: LinkElement["area1"];
  area2: LinkElement["area2"];
  filtersSynthesis?: Link["filters_synthesis"];
  filtersYear?: Link["filters_year"];
}>(n("CREATE_STUDY_LINK"));

export const deleteStudyLink = createAction<{
  studyId: FileStudyTreeConfigDTO["study_id"];
  area1: LinkElement["area1"];
  area2: LinkElement["area2"];
}>(n("DELETE_STUDY_LINK"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

const initDefaultAreaLinkSelection = (
  dispatch: AppDispatch,
  studyData?: FileStudyTreeConfigDTO,
): void => {
  if (studyData) {
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(""));
  } else {
    dispatch(setCurrentArea(""));
    dispatch(setCurrentLink(""));
    dispatch(setCurrentBindingConst(""));
  }
};

export const setDefaultAreaLinkSelection =
  (studyId: FileStudyTreeConfigDTO["study_id"]): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    const studyData = getStudySynthesis(state, studyId);
    initDefaultAreaLinkSelection(dispatch, studyData);
  };

export const createStudySynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("CREATE_STUDY_SYNTHESIS"), async (studyId, { dispatch, rejectWithValue }) => {
  try {
    // Fetch study synthesis data
    const studyData: FileStudyTreeConfigDTO = await api.getStudySynthesis(studyId);
    initDefaultAreaLinkSelection(dispatch, studyData);
    return studyData;
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const setStudySynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("SET_STUDY_SYNTHESIS"), (studyId, { rejectWithValue }) => {
  return api.getStudySynthesis(studyId).catch(rejectWithValue);
});

export const refreshStudySynthesis =
  (payload: GenericInfo | LaunchJobDTO): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    const id = "study_id" in payload ? payload.study_id : payload.id;

    if (getStudySynthesisIds(state).includes(id)) {
      dispatch(setStudySynthesis(id as string));

      if (getStudyMapsIds(state).includes(id)) {
        dispatch(setStudyMap(id as string));
      }
    }
  };

export const deleteStudySynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO["study_id"],
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("DELETE_STUDY_SYNTHESIS"), (id) => {
  // TODO Why empty?
  return id;
});

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudySynthesis.fulfilled, studySynthesesAdapter.addOne)
    .addCase(setStudySynthesis.fulfilled, studySynthesesAdapter.setOne)
    .addCase(updateStudySynthesis, studySynthesesAdapter.updateOne)
    .addCase(deleteStudySynthesis.fulfilled, studySynthesesAdapter.removeOne)
    .addCase(createStudyLink, (draftState, action) => {
      const filters = ["hourly", "daily", "weekly", "monthly", "annual"];
      const {
        studyId,
        area1,
        area2,
        filtersSynthesis = filters,
        filtersYear = filters,
      } = action.payload;

      const synthesis = draftState.entities[studyId];

      if (synthesis) {
        synthesis.areas[area1].links[area2] = {
          filters_synthesis: filtersSynthesis,
          filters_year: filtersYear,
        };
      }
    })
    .addCase(deleteStudyLink, (draftState, action) => {
      const { studyId, area1, area2 } = action.payload;
      delete draftState.entities[studyId]?.areas[area1].links[area2];
    })
    .addCase(setCurrentArea, (draftState, action) => {
      draftState.currentArea = action.payload;
    })
    .addCase(setCurrentLink, (draftState, action) => {
      draftState.currentLink = action.payload;
    })
    .addCase(setCurrentBindingConst, (draftState, action) => {
      draftState.currentBindingConst = action.payload;
    });
});
