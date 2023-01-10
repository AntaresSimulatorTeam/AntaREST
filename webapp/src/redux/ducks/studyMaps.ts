import {
  createAction,
  createAsyncThunk,
  createEntityAdapter,
  createReducer,
  EntityState,
} from "@reduxjs/toolkit";
import * as R from "ramda";
import {
  Area,
  AreaLayerColor,
  AreaLayerXandY,
  StudyMetadata,
  UpdateAreaUi,
} from "../../common/types";

import { AppAsyncThunkConfig, AppDispatch } from "../store";
import { makeActionName, makeLinkId } from "../utils";
import * as studyApi from "../../services/api/study";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import { getArea, getCurrentLayer, getStudyMapLayers } from "../selectors";
import * as studyDataApi from "../../services/api/studydata";
import { setCurrentArea } from "./studySyntheses";

export interface StudyMapNode {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
  layerX: AreaLayerXandY;
  layerY: AreaLayerXandY;
  layerColor: AreaLayerColor;
}

export interface StudyMapLink {
  id: string;
  // Props for react-d3-graph, don't rename them
  color?: string;
  strokeDasharray?: number[];
  strokeLinecap?: string;
  strokeWidth?: number;
}

export interface Layer {
  id: number;
  name: string;
  areas: StudyMapNode["id"][];
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: Record<StudyMapNode["id"], StudyMapNode>;
  links: Record<StudyMapLink["id"], StudyMapLink>;
  currentLayer?: Layer["id"];
}

export const studyMapsAdapter = createEntityAdapter<StudyMap>({
  selectId: (studyMap) => studyMap.studyId,
});

export interface StudyMapsState extends EntityState<StudyMap> {
  currentLayer: number;
  layers: Record<Layer["id"], Layer>;
}

const initialState = studyMapsAdapter.getInitialState({
  currentLayer: 0,
  layers: {},
}) as StudyMapsState;

const n = makeActionName("studyMaps");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

export const setCurrentLayer = createAction<
  NonNullable<StudyMap["currentLayer"]>
>(n("SET_CURRENT_LAYER"));

export const setLayers = createAction<NonNullable<Record<Layer["id"], Layer>>>(
  n("SET_LAYERS")
);

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

const refreshStudyMapLayers = (
  dispatch: AppDispatch,
  layers: Record<Layer["id"], Layer>
): void => {
  if (layers) {
    // Set Layers
    dispatch(setLayers(layers));
    // Set current layer
    dispatch(setCurrentLayer(layers[0].id));
  } else {
    dispatch(setLayers({}));
    dispatch(setCurrentLayer(0));
  }
};

export const fetchStudyMapLayers = createAsyncThunk<
  void,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(
  n("FETCH_STUDY_MAP_LAYERS"),
  async (studyId, { dispatch, rejectWithValue }) => {
    try {
      const layers = await studyApi.getStudyLayers(studyId);
      const studyMapLayers = layers.reduce((acc, { id, name, areas }) => {
        acc[id] = {
          id,
          name,
          areas,
        };
        return acc;
      }, {} as StudyMapsState["layers"]);
      refreshStudyMapLayers(dispatch, studyMapLayers);
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

async function getLinks(
  studyId: StudyMap["studyId"]
): Promise<StudyMap["links"]> {
  const links = await studyDataApi.getAllLinks({ uuid: studyId, withUi: true });
  return links.reduce((acc, link) => {
    const [style, linecap] = makeLinkStyle(link.ui?.style);
    const id = makeLinkId(link.area1, link.area2);
    acc[id] = {
      id,
      color: `rgb(${link.ui?.color}`,
      strokeDasharray: style,
      strokeLinecap: linecap,
      strokeWidth: link.ui?.width < 2 ? 2 : link.ui?.width,
    };
    return acc;
  }, {} as StudyMap["links"]);
}

async function getNodes(
  state: AppState,
  studyId: StudyMap["studyId"]
): Promise<StudyMap["nodes"]> {
  const areaPositions = await studyApi.getAreaPositions(studyId);
  return Object.keys(areaPositions).reduce((acc, areaId) => {
    const { ui, layerColor, layerX, layerY } = areaPositions[areaId];
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
      layerX,
      layerY,
      layerColor,
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
    newNode: StudyMapNode;
    studyId: StudyMetadata["id"];
    currentLayerId: Layer["id"];
  },
  { name: StudyMapNode["name"]; studyId: StudyMetadata["id"] },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_NODE"), async (data, { getState, rejectWithValue }) => {
  try {
    const { studyId, name } = data;
    const currentLayerId = getCurrentLayer(getState());
    const newNode = await studyDataApi.createArea(studyId, name);
    return { newNode, studyId, currentLayerId };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapNode = createAsyncThunk<
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
    currentLayerId: Layer["id"];
  },
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
  },
  AppAsyncThunkConfig
>(n("UPDATE_STUDY_MAP_NODE"), async (data, { getState, rejectWithValue }) => {
  const { studyId, nodeId, nodeUI } = data;
  const currentLayerId = getCurrentLayer(getState());
  try {
    await studyDataApi.updateAreaUI(studyId, nodeId, currentLayerId, nodeUI);
    return { studyId, nodeId, currentLayerId, nodeUI };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const deleteStudyMapNode = createAsyncThunk<
  {
    studyId: StudyMetadata["id"];
    nodeId: StudyMapNode["id"];
    currentLayerId: Layer["id"];
  },
  {
    studyId: StudyMetadata["id"];
    nodeId: StudyMapNode["id"];
  },
  AppAsyncThunkConfig
>(n("DELETE_STUDY_MAP_NODE"), async (data, { getState, rejectWithValue }) => {
  const { studyId, nodeId } = data;
  const currentLayerId = getCurrentLayer(getState());
  try {
    await studyDataApi.deleteArea(studyId, nodeId);
    return { studyId, nodeId, currentLayerId };
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

export const createStudyMapLayer = createAsyncThunk<
  {
    newLayerId: Layer["id"];
    name: Layer["name"];
  },
  { name: Layer["name"]; studyId: StudyMetadata["id"] },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_LAYER"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, name } = data;
    const newLayerId = await studyApi.createStudyLayer(studyId, name);
    return { newLayerId, name };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapLayer = createAsyncThunk<
  {
    layerId: Layer["id"];
    name: Layer["name"];
    areas?: StudyMapNode[];
  },
  {
    studyId: StudyMetadata["id"];
    layerId: Layer["id"];
    name: Layer["name"];
    areas?: StudyMapNode[];
  },
  AppAsyncThunkConfig
>(n("UPDATE_STUDY_MAP_LAYER"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, layerId, name, areas } = data;
    await studyApi.updateStudyLayer(studyId, layerId, name, areas);
    return { layerId, name, areas };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const deleteStudyMapLayer = createAsyncThunk<
  {
    layerId: Layer["id"];
  },
  { studyId: StudyMetadata["id"]; layerId: Layer["id"] },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_LAYER"),
  async (data, { getState, dispatch, rejectWithValue }) => {
    try {
      const { studyId, layerId } = data;
      const layers = getStudyMapLayers(getState());
      await studyApi.deleteStudyLayer(studyId, layerId);
      refreshStudyMapLayers(dispatch, layers);
      dispatch(setCurrentArea(""));
      return { layerId };
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

////////////////////////////////////////////////////////////////
// Reducer
////////////////////////////////////////////////////////////////

export default createReducer(initialState, (builder) => {
  builder
    .addCase(createStudyMap.fulfilled, studyMapsAdapter.addOne)
    .addCase(setStudyMap.fulfilled, studyMapsAdapter.setOne)
    .addCase(createStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, newNode, currentLayerId } = action.payload;
      const entity = draftState.entities[studyId];
      if (entity) {
        entity.nodes[newNode.id] = {
          id: newNode.id,
          name: newNode.name,
          x: 0,
          y: 0,
          layerX: { 0: 0 },
          layerY: { 0: 0 },
          layerColor: { 0: NODE_COLOR.slice(4, -1) },
          color: NODE_COLOR.slice(4, -1),
          rgbColor: NODE_COLOR.slice(4, -1).split(",").map(Number),
          size: {
            width: getNodeWidth(newNode.name),
            height: NODE_HEIGHT,
          },
        };
        draftState.layers[currentLayerId].areas.push(newNode.id);
        draftState.layers[0].areas.push(newNode.id);
      }
    })
    .addCase(deleteStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, nodeId } = action.payload;
      const entity = draftState.entities[studyId];
      if (entity) {
        delete entity.nodes[nodeId];
      }
    })
    .addCase(updateStudyMapNode.fulfilled, (draftState, action) => {
      const { studyId, nodeId, currentLayerId, nodeUI } = action.payload;
      const entity = draftState.entities[studyId];
      if (entity) {
        const color = nodeUI.color_rgb;
        const { x, y, layerX, layerY, layerColor } = nodeUI;
        const updatedLayerX = { ...layerX, [currentLayerId]: x };
        const updatedLayerY = { ...layerY, [currentLayerId]: y };
        const updatedLayerColor = {
          ...layerColor,
          [currentLayerId]: `${color[0]}, ${color[1]}, ${color[2]}`,
        };
        entity.nodes[nodeId] = {
          ...entity.nodes[nodeId],
          x,
          y,
          layerX: updatedLayerX,
          layerY: updatedLayerY,
          layerColor: updatedLayerColor,
          color: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
          rgbColor: [color[0], color[1], color[2]],
        };
      }
    })
    .addCase(setCurrentLayer, (draftState, action) => {
      draftState.currentLayer = action.payload;
    })
    .addCase(setLayers, (draftState, action) => {
      draftState.layers = action.payload;
    })
    .addCase(createStudyMapLayer.fulfilled, (draftState, action) => {
      const { newLayerId, name } = action.payload;
      draftState.layers[newLayerId] = {
        id: newLayerId,
        name,
        areas: [],
      };
    })
    .addCase(updateStudyMapLayer.fulfilled, (draftState, action) => {
      const { layerId, name, areas } = action.payload;
      if (areas) {
        draftState.layers[layerId] = {
          ...draftState.layers[layerId],
          name,
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          areas: [...areas],
        };
      }
      draftState.layers[layerId] = {
        ...draftState.layers[layerId],
        name,
      };
    })
    .addCase(deleteStudyMapLayer.fulfilled, (draftState, action) => {
      const { layerId } = action.payload;
      delete draftState.layers[layerId];
    });
});
