import {
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
} from "@reduxjs/toolkit";
import * as RA from "ramda-adjunct";
import {
  FileStudyTreeConfigDTO,
  SynthesisSummary,
  WSMessage,
} from "../../common/types";
import * as api from "../../services/api/study";
import { AppAsyncThunkConfig } from "../store";
import { makeActionName, Status } from "../utils";

// const MAX_SYNTHESIS_ELEMENTS = 10;

/* type WithStatusCode<T> = {
  status: Status;
  error?: string;
} & T;*/

export const synthesisAdapter = createEntityAdapter<FileStudyTreeConfigDTO>({
  selectId: (synthesis) => synthesis.study_id,
});

export interface SynthesisState
  extends ReturnType<typeof synthesisAdapter.getInitialState> {
  status: Status;
  error?: string;
}

const initialState = synthesisAdapter.getInitialState({
  status: Status.Idle,
  error: null as string | null,
}) as SynthesisState;

const n = makeActionName("synthesis");

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

export const createSynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO,
  FileStudyTreeConfigDTO["study_id"],
  AppAsyncThunkConfig
>(n("CREATE_SYNTHESIS"), async (arg, { getState, rejectWithValue }) => {
  try {
    // if (getState().synthesis.ids.length >= MAX_SYNTHESIS_ELEMENTS)
    //   throw Error("MAX SYNTHESIS ELEMENTS");
    return api.getStudySynthesis(arg);
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const setSynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO,
  WSMessage<SynthesisSummary>,
  AppAsyncThunkConfig
>(n("SET_SYNTHESIS"), (event, { rejectWithValue }) => {
  // eslint-disable-next-line camelcase
  const { study_id } = event.payload;
  return api.getStudySynthesis(study_id).catch(rejectWithValue);
});

export const deleteSynthesis = createAsyncThunk<
  FileStudyTreeConfigDTO["study_id"],
  FileStudyTreeConfigDTO["study_id"] | WSMessage<SynthesisSummary>,
  AppAsyncThunkConfig
>(
  n("DELETE_SYNTHESIS"),
  async (arg, { dispatch, getState, rejectWithValue }) => {
    let studyId: string;

    if (RA.isString(arg)) {
      studyId = arg;
    } else {
      studyId = arg.payload.study_id;
    }

    return studyId;
  }
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createSynthesis.pending, (draftState) => {
      draftState.status = Status.Loading;
    })
    .addCase(createSynthesis.rejected, (draftState, action) => {
      if (action.error.message === "MAX SYNTHESIS ELEMENTS") {
        synthesisAdapter.removeAll(draftState);
        // synthesisAdapter.addOne(draftState, action);
      } else {
        draftState.status = Status.Failed;
        draftState.error = action.error.message;
      }
    })
    .addCase(createSynthesis.fulfilled, synthesisAdapter.addOne)
    .addCase(setSynthesis.fulfilled, synthesisAdapter.setOne)
    .addCase(deleteSynthesis.fulfilled, synthesisAdapter.removeOne);
});
