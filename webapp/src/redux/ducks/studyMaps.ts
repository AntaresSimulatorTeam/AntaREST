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
  AreaLayerPosition,
  LinkElement,
  StudyLayer,
  StudyMetadata,
  UpdateAreaUi,
} from "../../common/types";

import { AppAsyncThunkConfig, AppDispatch } from "../store";
import { makeActionName, makeLinkId, parseLinkId } from "../utils";
import * as studyApi from "../../services/api/study";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import {
  getArea,
  getCurrentLayer,
  getStudyMap,
  getStudyMapLayersById,
  getStudySynthesis,
} from "../selectors";
import * as studyDataApi from "../../services/api/studydata";
import {
  createStudyLink,
  deleteStudyLink,
  setCurrentArea,
} from "./studySyntheses";

export interface StudyMapNode {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
  layerX: AreaLayerPosition;
  layerY: AreaLayerPosition;
  layerColor: AreaLayerColor;
}

export interface StudyMapLink {
  id: string;
  temp?: boolean;
  // Props for react-d3-graph, don't rename them
  color?: string;
  strokeDasharray?: number[];
  strokeLinecap?: string;
  strokeWidth?: number;
  mouseCursor?: string;
  opacity?: number;
}

export interface StudyMapDistrict {
  id: string;
  name: string;
  output: boolean;
  comments: string;
  areas: Array<StudyMapNode["id"]>;
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: Record<StudyMapNode["id"], StudyMapNode>;
  links: Record<StudyMapLink["id"], StudyMapLink>;
  currentLayer?: StudyLayer["id"];
}

export const studyMapsAdapter = createEntityAdapter<StudyMap>({
  selectId: (studyMap) => studyMap.studyId,
});

export interface StudyMapsState extends EntityState<StudyMap> {
  currentLayer: StudyLayer["id"];
  layers: Record<StudyLayer["id"], StudyLayer>;
  districts: Record<StudyMapDistrict["id"], StudyMapDistrict>;
}

const initialState = studyMapsAdapter.getInitialState({
  currentLayer: "0",
  layers: {},
  districts: {},
}) as StudyMapsState;

const n = makeActionName("studyMaps");

////////////////////////////////////////////////////////////////
// Action Creators
////////////////////////////////////////////////////////////////

const createStudyMapNodeTemp = createAction<{
  studyId: StudyMetadata["id"];
  node: StudyMapNode;
}>(n("CREATE_STUDY_MAP_NODE_TEMP"));

const deleteStudyMapNodeTemp = createAction<{
  studyId: StudyMetadata["id"];
  nodeId: StudyMapNode["id"];
}>(n("DELETE_STUDY_MAP_NODE_TEMP"));

const createStudyMapLinkTemp = createAction<{
  studyId: StudyMetadata["id"];
  link: StudyMapLink;
}>(n("CREATE_STUDY_MAP_LINK_TEMP"));

const deleteStudyMapLinkTemp = createAction<{
  studyId: StudyMetadata["id"];
  linkId: StudyMapLink["id"];
}>(n("DELETE_STUDY_MAP_LINK_TEMP"));

export const setCurrentLayer = createAction<
  NonNullable<StudyMap["currentLayer"]>
>(n("SET_CURRENT_LAYER"));

export const setLayers = createAction<
  NonNullable<Record<StudyLayer["id"], StudyLayer>>
>(n("SET_LAYERS"));

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

const initStudyMapLayers = (
  dispatch: AppDispatch,
  layers: Record<StudyLayer["id"], StudyLayer>
): void => {
  if (layers) {
    dispatch(setLayers(layers));
    dispatch(setCurrentLayer(layers["0"].id));
  } else {
    dispatch(setLayers({}));
    dispatch(setCurrentLayer("0"));
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
      initStudyMapLayers(dispatch, studyMapLayers);
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
    currentLayerId: StudyLayer["id"];
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
    currentLayerId: StudyLayer["id"];
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
  void, // WebSocket will update it
  {
    studyId: StudyMetadata["id"];
    nodeId: StudyMapNode["id"];
  },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_NODE"),
  async (data, { dispatch, getState, rejectWithValue }) => {
    const { studyId, nodeId } = data;
    const state = getState();
    const node = getStudyMap(state, studyId)?.nodes[nodeId];

    if (node) {
      dispatch(deleteStudyMapNodeTemp({ studyId, nodeId }));

      try {
        await studyDataApi.deleteArea(studyId, nodeId);
      } catch (error) {
        dispatch(createStudyMapNodeTemp({ studyId, node }));
        return rejectWithValue(error);
      }
    }
  }
);

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

export const createStudyMapLink = createAsyncThunk<
  void, // WebSocket will update it
  {
    studyId: StudyMetadata["id"];
    area1: LinkElement["area1"];
    area2: LinkElement["area2"];
  },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_LINK"), async (data, { dispatch, rejectWithValue }) => {
  const { studyId, area1, area2 } = data;
  const linkId = makeLinkId(area1, area2);

  dispatch(createStudyLink({ studyId, area1, area2 }));

  dispatch(
    createStudyMapLinkTemp({
      studyId,
      link: {
        id: linkId,
        temp: true,
        opacity: 0.3,
        mouseCursor: "wait", // TODO not working
      },
    })
  );

  try {
    await studyDataApi.createLink(studyId, { area1, area2 });
  } catch (err) {
    dispatch(deleteStudyLink({ studyId, area1, area2 }));
    dispatch(deleteStudyMapLinkTemp({ studyId, linkId }));

    return rejectWithValue(err);
  }
});

export const deleteStudyMapLink = createAsyncThunk<
  void, // WebSocket will update it
  {
    studyId: StudyMetadata["id"];
    linkId: LinkElement["id"];
  },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_LINK"),
  async (data, { getState, dispatch, rejectWithValue }) => {
    const { studyId, linkId } = data;
    const [area1, area2] = parseLinkId(linkId);
    const state = getState();
    const link = getStudySynthesis(state, studyId)?.areas[area1].links[area2];

    if (link) {
      dispatch(deleteStudyLink({ studyId, area1, area2 }));

      try {
        await studyDataApi.deleteLink(studyId, area1, area2);
      } catch (err) {
        dispatch(createStudyLink({ ...link, studyId, area1, area2 }));

        return rejectWithValue(err);
      }
    }
  }
);
export const createStudyMapLayer = createAsyncThunk<
  {
    newLayerId: StudyLayer["id"];
    name: StudyLayer["name"];
  },
  { name: StudyLayer["name"]; studyId: StudyMetadata["id"] },
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
    layerId: StudyLayer["id"];
    name: StudyLayer["name"];
    areas?: StudyLayer["areas"];
  },
  {
    studyId: StudyMetadata["id"];
    layerId: StudyLayer["id"];
    name: StudyLayer["name"];
    areas?: StudyLayer["areas"];
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
    layerId: StudyLayer["id"];
  },
  { studyId: StudyMetadata["id"]; layerId: StudyLayer["id"] },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_LAYER"),
  async (data, { getState, dispatch, rejectWithValue }) => {
    try {
      const { studyId, layerId } = data;
      const layers = getStudyMapLayersById(getState());
      await studyApi.deleteStudyLayer(studyId, layerId);
      initStudyMapLayers(dispatch, layers);
      dispatch(setCurrentArea(""));
      return { layerId };
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const fetchStudyMapDistricts = createAsyncThunk<
  Record<StudyMapDistrict["id"], StudyMapDistrict>,
  StudyMap["studyId"],
  AppAsyncThunkConfig
>(
  n("FETCH_STUDY_MAP_DISTRICTS"),
  async (studyId, { dispatch, rejectWithValue }) => {
    try {
      const districts = await studyApi.getStudyDistricts(studyId);
      const studyMapDistricts = districts.reduce(
        (acc, { id, name, output, comments, areas }) => {
          acc[id] = {
            id,
            name,
            output,
            comments,
            areas,
          };
          return acc;
        },
        {} as StudyMapsState["districts"]
      );
      return studyMapDistricts;
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

export const createStudyMapDistrict = createAsyncThunk<
  StudyMapDistrict,
  {
    studyId: StudyMetadata["id"];
    name: StudyMapDistrict["name"];
    output: StudyMapDistrict["output"];
    comments: StudyMapDistrict["comments"];
  },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_DISTRICT"), async (data, { rejectWithValue }) => {
  try {
    const { name, output, studyId } = data;
    const { id, comments, areas } = await studyApi.createStudyDistrict(
      studyId,
      name,
      output,
      data.comments
    );
    return { id, name, output, comments, areas };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapDistrict = createAsyncThunk<
  {
    districtId: StudyMapDistrict["id"];
    output: StudyMapDistrict["output"];
    comments: StudyMapDistrict["comments"];
    areas?: StudyMapDistrict["areas"];
  },
  {
    studyId: StudyMetadata["id"];
    districtId: StudyMapDistrict["id"];
    output: StudyMapDistrict["output"];
    comments: StudyMapDistrict["comments"];
    areas?: StudyMapDistrict["areas"];
  }
>(n("UPDATE_STUDY_MAP_DISTRICT"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, districtId, output, comments, areas } = data;
    await studyApi.updateStudyDistrict(
      studyId,
      districtId,
      output,
      comments,
      areas
    );
    return { districtId, output, comments, areas };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const deleteStudyMapDistrict = createAsyncThunk<
  {
    districtId: StudyMapDistrict["id"];
  },
  { studyId: StudyMetadata["id"]; districtId: StudyMapDistrict["id"] },
  AppAsyncThunkConfig
>(n("DELETE_STUDY_MAP_DISTRICT"), async (data, { rejectWithValue }) => {
  try {
    const { studyId, districtId } = data;
    await studyApi.deleteStudyDistrict(studyId, districtId);
    return { districtId };
  } catch (error) {
    return rejectWithValue(error);
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

        draftState.layers["0"].areas.push(newNode.id);
        if (currentLayerId !== "0") {
          draftState.layers[currentLayerId].areas.push(newNode.id);
        }
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
    .addCase(createStudyMapNodeTemp, (draftState, action) => {
      const { studyId, node } = action.payload;
      const studyMap = draftState.entities[studyId];
      if (studyMap) {
        studyMap.nodes[node.id] = node;
      }
    })
    .addCase(deleteStudyMapNodeTemp, (draftState, action) => {
      const { studyId, nodeId } = action.payload;
      delete draftState.entities[studyId]?.nodes[nodeId];
    })
    .addCase(createStudyMapLinkTemp, (draftState, action) => {
      const { studyId, link } = action.payload;
      const studyMap = draftState.entities[studyId];
      if (studyMap) {
        studyMap.links[link.id] = link;
      }
    })
    .addCase(deleteStudyMapLinkTemp, (draftState, action) => {
      const { studyId, linkId } = action.payload;
      delete draftState.entities[studyId]?.links[linkId];
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
      draftState.layers[layerId].name = name;
      if (areas) {
        draftState.layers[layerId].areas = areas;
      }
    })
    .addCase(deleteStudyMapLayer.fulfilled, (draftState, action) => {
      const { layerId } = action.payload;
      delete draftState.layers[layerId];
    })
    .addCase(fetchStudyMapDistricts.fulfilled, (draftState, action) => {
      draftState.districts = action.payload;
    })
    .addCase(createStudyMapDistrict.fulfilled, (draftState, action) => {
      const { id, name, output, comments, areas } = action.payload;
      draftState.districts[id] = {
        id,
        name,
        output,
        comments,
        areas,
      };
    })
    .addCase(deleteStudyMapDistrict.fulfilled, (draftState, action) => {
      const { districtId } = action.payload;
      delete draftState.districts[districtId];
    })
    .addCase(updateStudyMapDistrict.fulfilled, (draftState, action) => {
      const { districtId, output, comments, areas } = action.payload;
      draftState.districts[districtId].output = output;
      draftState.districts[districtId].comments = comments;
      if (areas) {
        draftState.districts[districtId].areas = areas;
      }
    });
});
