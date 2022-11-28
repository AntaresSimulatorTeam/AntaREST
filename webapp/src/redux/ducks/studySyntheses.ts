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
import { getStudySynthesis, getStudySynthesisIds } from "../selectors";
import { AppAsyncThunkConfig, AppDispatch, AppThunk } from "../store";
import { makeActionName } from "../utils";

export const studySynthesesAdapter =
  createEntityAdapter<FileStudyTreeConfigDTO>({
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

export const setCurrentArea = createAction<
  NonNullable<StudySynthesesState["currentArea"]>
>(n("SET_CURRENT_AREA"));

export const setCurrentLink = createAction<
  NonNullable<StudySynthesesState["currentLink"]>
>(n("SET_CURRENT_LINK"));

export const setCurrentBindingConst = createAction<
  NonNullable<StudySynthesesState["currentBindingConst"]>
>(n("SET_CURRENT_BINDING_CONST"));

export const updateStudySynthesis = createAction<{
  id: FileStudyTreeConfigDTO["study_id"];
  changes: Partial<Omit<FileStudyTreeConfigDTO, "study_id">>;
}>(n("SET_STUDY_SYNTHESIS"));

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

const initDefaultAreaLinkSelection = (
  dispatch: AppDispatch,
  studyData?: FileStudyTreeConfigDTO
): void => {
  if (studyData) {
    // Set current area
    const areas = Object.keys(studyData.areas);
    if (areas.length > 0) {
      dispatch(setCurrentArea(areas[0]));
    } else {
      dispatch(setCurrentArea(""));
    }

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
>(
  n("CREATE_STUDY_SYNTHESIS"),
  async (studyId, { dispatch, getState, rejectWithValue }) => {
    try {
      // Fetch study synthesis data
      const studyData: FileStudyTreeConfigDTO = await api.getStudySynthesis(
        studyId
      );
      initDefaultAreaLinkSelection(dispatch, studyData);
      return studyData;
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

export const setStudySynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO,
  WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("SET_STUDY_SYNTHESIS"), (event, { rejectWithValue }) => {
  const { id } = event.payload;
  return api.getStudySynthesis(id as string).catch(rejectWithValue);
});

export const refreshStudySynthesis =
  (event: WSMessage<GenericInfo>): AppThunk =>
  (dispatch, getState) => {
    const state = getState();
    if (getStudySynthesisIds(state).indexOf(event.payload.id) !== -1) {
      dispatch(setStudySynthesis(event));
    }
  };

export const deleteStudySynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO["study_id"],
  FileStudyTreeConfigDTO["study_id"] | WSMessage<GenericInfo>,
  AppAsyncThunkConfig
>(n("DELETE_STUDY_SYNTHESIS"), async (arg) => {
  return RA.isString(arg) ? arg : (arg.payload.id as string);
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
