import {
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
  EntityState,
} from "@reduxjs/toolkit";
import { Area, StudyMetadata } from "../../common/types";
import { AppAsyncThunkConfig } from "../store";
import { makeActionName } from "../utils";
import * as api from "../../services/api/study";
import {
  getNodeWidth,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import { getArea } from "../selectors";

export interface AreaNode {
  id: string;
  areaName: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: AreaNode[];
}

export const studyMapsAdapter = createEntityAdapter<StudyMap>({
  selectId: (studyMap) => studyMap.studyId,
});

export type StudyMapsState = EntityState<StudyMap>;

const initialState = studyMapsAdapter.getInitialState() as StudyMapsState;

const n = makeActionName("studyMaps");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

// TODO

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

async function getNodes(
  state: AppState,
  studyId: StudyMetadata["id"]
): Promise<AreaNode[]> {
  const areaPositions = await api.getAreaPositions(studyId);
  return Object.keys(areaPositions).map((areaId) => {
    const { ui } = areaPositions[areaId];
    const rgb = [ui.color_r, ui.color_g, ui.color_b];
    const area = getArea(state, areaId) as Area;

    return {
      id: areaId,
      areaName: area.name,
      x: ui.x,
      y: ui.y,
      color: `rgb(${rgb.join(", ")})`,
      rgbColor: rgb,
      size: { width: getNodeWidth(areaId), height: NODE_HEIGHT },
    };
  });
}

export const createStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return { studyId, nodes: await getNodes(getState(), studyId) };
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const setStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("SET_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return { studyId, nodes: await getNodes(getState(), studyId) };
  } catch (err) {
    return rejectWithValue(err);
  }
});

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudyMap.fulfilled, studyMapsAdapter.addOne)
    .addCase(setStudyMap.fulfilled, studyMapsAdapter.setOne);
});
