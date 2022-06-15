import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import * as RA from "ramda-adjunct";
import {
  FileStudyTreeConfigDTO,
  GenericInfo,
  WSMessage,
} from "../../common/types";
import * as api from "../../services/api/study";
import { selectLinks } from "../selectors";
import { AppAsyncThunkConfig } from "../store";
import { makeActionName } from "../utils";

export const studyDataAdapter = createEntityAdapter<FileStudyTreeConfigDTO>({
  selectId: (studyData) => studyData.study_id,
});

export interface StudyDataState
  extends ReturnType<typeof studyDataAdapter.getInitialState> {
  currentArea: string;
  currentLink: string;
}

const initialState = studyDataAdapter.getInitialState({
  currentArea: "",
  currentLink: "",
}) as StudyDataState;

const n = makeActionName("studyDataSynthesis");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentArea = createAction<
  NonNullable<StudyDataState["currentArea"]>
>(n("SET_CURRENT_AREA"));

export const setCurrentLink = createAction<
  NonNullable<StudyDataState["currentLink"]>
>(n("SET_CURRENT_LINK"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(
  n("CREATE_STUDY_DATA"),
  async (studyId, { dispatch, getState, rejectWithValue }) => {
    try {
      // Fetch study synthesis data
      const studyData = await api.getStudySynthesis(studyId);

      // Set current area
      const areas = Object.keys(studyData.areas);
      if (areas.length > 0) dispatch(setCurrentArea(areas[0]));

      // Set current link
      const links = selectLinks(studyData);
      const linkList = links ? Object.values(links) : [];
      if (linkList.length > 0) {
        dispatch(setCurrentLink(linkList[0].name));
      }

      return studyData;
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

export const setStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO,
  WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("SET_STUDY_DATA"), (event, { rejectWithValue }) => {
  const { id } = event.payload;
  return api.getStudySynthesis(id as string).catch(rejectWithValue);
});

export const deleteStudyData = createAsyncThunk<
  FileStudyTreeConfigDTO["study_id"],
  FileStudyTreeConfigDTO["study_id"] | WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("DELETE_STUDY_DATA"), async (arg, elm) => {
  if (RA.isString(arg)) {
    return arg;
  }

  return arg.payload.id as string;
});

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudyData.fulfilled, studyDataAdapter.addOne)
    .addCase(setStudyData.fulfilled, studyDataAdapter.setOne)
    .addCase(deleteStudyData.fulfilled, studyDataAdapter.removeOne)
    .addCase(setCurrentArea, (draftState, action) => {
      draftState.currentArea = action.payload;
    })
    .addCase(setCurrentLink, (draftState, action) => {
      draftState.currentLink = action.payload;
    });
});
