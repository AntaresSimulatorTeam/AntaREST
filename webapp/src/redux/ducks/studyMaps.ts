import {
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
  EntityState,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import {
  Area,
  AreaInfoDTO,
  StudyMetadata,
  UpdateAreaUi,
} from "../../common/types";

import { AppAsyncThunkConfig } from "../store";
import { makeActionName } from "../utils";
import * as api from "../../services/api/study";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import { getArea } from "../selectors";
import {
  createArea,
  getAllLinks,
  updateAreaUI,
} from "../../services/api/studydata";

export interface AreaNode {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
}

export interface AreaNodeLink {
  id: string;
  // Props for react-d3-graph, don't rename them
  color: string;
  strokeDasharray: number[];
  strokeLinecap: string;
  strokeWidth: number;
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: Record<AreaNode["id"], AreaNode>;
  links: Record<AreaNodeLink["id"], AreaNodeLink>;
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

////////////////////////////////////////////////////////////////
// Thunks
////////////////////////////////////////////////////////////////

type LinkStyle = [number[], string];

const makeLinkStyle = R.cond<[string], LinkStyle>([
  [R.equals("dot"), (): LinkStyle => [[1, 5], "round"]],
  [R.equals("dash"), (): LinkStyle => [[16, 8], "square"]],
  [R.equals("dotdash"), (): LinkStyle => [[10, 6, 1, 6], "square"]],
  [R.T, (): LinkStyle => [[0], "butt"]],
]);

async function getLinks(
  studyId: StudyMetadata["id"]
): Promise<StudyMap["links"]> {
  const allLinks = await getAllLinks({ uuid: studyId, withUi: true });
  return allLinks.reduce((acc, link) => {
    const [style, linecap] = makeLinkStyle(link.ui?.style);
    const id = `${link.area1} / ${link.area2}`;
    acc[id] = {
      id,
      color: `rgb(${link.ui?.color}`,
      strokeDasharray: style,
      strokeLinecap: linecap,
      strokeWidth: link.ui?.width < 2 ? 2 : link.ui?.width, // Sets minimum link width to 2
    };
    return acc;
  }, {} as StudyMap["links"]);
}

async function getNodes(
  state: AppState,
  studyId: StudyMetadata["id"]
): Promise<StudyMap["nodes"]> {
  const areaPositions = await api.getAreaPositions(studyId);
  return Object.keys(areaPositions).reduce((acc, areaId) => {
    const { ui } = areaPositions[areaId];
    const rgb = [ui.color_r, ui.color_g, ui.color_b];
    const area = getArea(state, studyId, areaId) as Area;
    acc[areaId] = {
      id: areaId,
      name: area.name,
      x: ui.x,
      y: ui.y,
      color: `rgb(${rgb.join(", ")})`,
      rgbColor: rgb,
      size: { width: getNodeWidth(areaId), height: NODE_HEIGHT },
    };
    return acc;
  }, {} as StudyMap["nodes"]);
}

export const createStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return {
      studyId,
      nodes: await getNodes(getState(), studyId),
      links: await getLinks(studyId),
    };
  } catch (err) {
    return rejectWithValue(err);
  }
});

export const createStudyMapNode = createAsyncThunk<
  {
    newArea: AreaInfoDTO;
    studyId: StudyMetadata["id"];
  },
  { name: AreaInfoDTO["name"]; studyId: StudyMetadata["id"] },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_NODE"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, name } = data;
    const newArea = await createArea(studyId, name);
    return { newArea, studyId };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapNode = createAsyncThunk<
  {
    studyId: StudyMetadata["id"];
    nodeId: AreaNode["id"];
    nodeUI: UpdateAreaUi;
  },
  {
    studyId: StudyMetadata["id"];
    nodeId: AreaNode["id"];
    nodeUI: UpdateAreaUi;
  },
  AppAsyncThunkConfig
>(n("UPDATE_STUDY_MAP_NODE"), async (data, { rejectWithValue }) => {
  const { studyId, nodeId, nodeUI } = data;

  try {
    await updateAreaUI(studyId, nodeId, nodeUI);
    return { studyId, nodeId, nodeUI };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const setStudyMap = createAsyncThunk<
  StudyMap,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(n("SET_STUDY_MAP"), async (studyId, { getState, rejectWithValue }) => {
  try {
    return {
      studyId,
      nodes: await getNodes(getState(), studyId),
      links: await getLinks(studyId),
    };
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
    .addCase(setStudyMap.fulfilled, studyMapsAdapter.setOne)
    .addCase(createStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, newArea } = action.payload;
      const entity = draftState.entities[studyId];
      if (entity) {
        entity.nodes[newArea.id] = {
          id: newArea.id,
          name: newArea.name,
          x: 0,
          y: 0,
          color: NODE_COLOR,
          rgbColor: NODE_COLOR.slice(4, -1).split(",").map(Number),
          size: {
            width: getNodeWidth(newArea.name),
            height: NODE_HEIGHT,
          },
        };
      }
    })
    .addCase(updateStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, nodeId, nodeUI } = action.payload;

      const entity = draftState.entities[studyId];
      if (entity) {
        const color = nodeUI.color_rgb;
        entity.nodes[nodeId] = {
          ...entity.nodes[nodeId],
          x: nodeUI.x,
          y: nodeUI.y,
          color: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
          rgbColor: [color[0], color[1], color[2]],
        };
      }
    });
});
