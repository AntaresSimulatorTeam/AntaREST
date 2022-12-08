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
  AreaInfoDTO,
  StudyMetadata,
  UpdateAreaUi,
} from "../../common/types";

import { AppAsyncThunkConfig, AppDispatch } from "../store";
import { makeActionName } from "../utils";
import * as api from "../../services/api/study";
import {
  getNodeWidth,
  NODE_COLOR,
  NODE_HEIGHT,
} from "../../components/App/Singlestudy/explore/Modelization/Map/utils";
import { AppState } from ".";
import {
  getArea,
  getCurrentAreaLinks,
  getStudyMapLinks,
  isStudyMapLinkExist,
} from "../selectors";
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
  isDeleting?: boolean;
}

export interface StudyMapLink {
  id: string;
  isTemp?: boolean;
  isDeleting?: boolean;
  // Props for react-d3-graph, don't rename them
  color?: string;
  strokeDasharray?: number[];
  strokeLinecap?: string;
  strokeWidth?: number;
}

export interface Layer {
  id: string;
  name: string;
  areas: AreaNode[];
}

export interface StudyMap {
  studyId: StudyMetadata["id"];
  nodes: Record<AreaNode["id"], AreaNode>;
  links: Record<AreaNodeLink["id"], AreaNodeLink>;
  currentLayer?: Layer["id"];
}

export const studyMapsAdapter = createEntityAdapter<StudyMap>({
  selectId: (studyMap) => studyMap.studyId,
});

export interface StudyMapsState extends EntityState<StudyMap> {
  currentLayer: string;
  layers: Record<Layer["id"], Layer>;
}

const initialState = studyMapsAdapter.getInitialState({
  currentLayer: "",
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

const initStudyMapLayers = (
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
    dispatch(setCurrentLayer(""));
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
      const layers = await api.getStudyLayers(studyId);

      const studyMapLayers = layers.reduce((acc, { id, name, areas }) => {
        acc[id] = {
          id,
          name,
          areas,
        };
        return acc;
      }, {} as StudyMapsState["layers"]);

      if (studyMapLayers) {
        initStudyMapLayers(dispatch, studyMapLayers);
      }
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

async function getLinks(
  studyId: StudyMap["studyId"]
): Promise<StudyMap["links"]> {
  const links = await getAllLinks({ uuid: studyId, withUi: true });
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
    studyId: StudyMap["studyId"];
  },
  { name: AreaInfoDTO["name"]; studyId: StudyMap["studyId"] },
  AppAsyncThunkConfig
>(n("CREATE_STUDY_MAP_NODE"), async (data, { dispatch, rejectWithValue }) => {
  try {
    const { studyId, name } = data;

    const newArea = await studyDataApi.createArea(studyId, name);
    return { newArea, studyId };
  } catch (error) {
    return rejectWithValue(error);
  }
});

export const updateStudyMapNode = createAsyncThunk<
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
  },
  {
    studyId: StudyMap["studyId"];
    nodeId: StudyMapNode["id"];
    nodeUI: UpdateAreaUi;
  },
  AppAsyncThunkConfig
>(n("UPDATE_STUDY_MAP_NODE"), async (data, { rejectWithValue }) => {
  const { studyId, nodeId, nodeUI } = data;

  try {
    await studyDataApi.updateAreaUI(studyId, nodeId, nodeUI);
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

export const createStudyMapLink = createAsyncThunk<
  { studyId: StudyMap["studyId"]; linkId: StudyMapLink["id"] },
  {
    studyId: StudyMap["studyId"];
    sourceId: StudyMapNode["id"];
    targetId: StudyMapNode["id"];
  },
  AppAsyncThunkConfig
>(
  n("CREATE_STUDY_MAP_LINK"),
  async (args, { dispatch, rejectWithValue }) => {
    const { studyId, sourceId, targetId } = args;

    dispatch(createStudyMapLinkTemp(args));

    try {
      await studyDataApi.createLink(studyId, {
        area1: sourceId,
        area2: targetId,
      });

      return { studyId, linkId: makeLinkId(sourceId, targetId) };
    } catch (err) {
      return rejectWithValue(err);
    }
  },
  {
    condition: ({ studyId, sourceId, targetId }, { getState }) =>
      !isStudyMapLinkExist(getState(), studyId, makeLinkId(sourceId, targetId)),
    serializeError: () => new Error("Link already exist"),
  }
);

export const deleteStudyMapLink = createAsyncThunk<
  { studyId: StudyMap["studyId"]; linkId: StudyMapLink["id"] },
  {
    studyId: StudyMap["studyId"];
    id: StudyMapLink["id"];
  },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_LINK"),
  async ({ studyId, id }, { dispatch, rejectWithValue }) => {
    dispatch(
      updateStudyMapLink({ id, studyId, changes: { isDeleting: true } })
    );

    try {
      await studyDataApi.deleteLink(studyId, ...parseLinkId(id));
      return { studyId, linkId: id };
    } catch (err) {
      return rejectWithValue(err);
    }
  }
);

export const deleteStudyMapNode = createAsyncThunk<
  { studyId: StudyMap["studyId"]; areaId: StudyMapNode["id"] },
  {
    studyId: StudyMap["studyId"];
    areaId: StudyMapNode["id"];
  },
  AppAsyncThunkConfig
>(
  n("DELETE_STUDY_MAP_NODE"),
  async (data, { getState, dispatch, rejectWithValue }) => {
    const { studyId, areaId } = data;

    const state = getState();
    const areaLinks = getCurrentAreaLinks(state, studyId);
    const studyLinks = getStudyMapLinks(state, studyId);

    dispatch(
      updateStudyMapNodeLinks({
        areaLinks,
        studyLinks,
        areaId,
        studyId,
        changes: { isDeleting: true },
      })
    );

    try {
      await studyDataApi.deleteArea(studyId, areaId);
      dispatch(setCurrentArea(""));
      return { studyId, areaId };
    } catch (err) {
      dispatch(setCurrentArea(""));
      return rejectWithValue(err);
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
    })
    .addCase(setCurrentLayer, (draftState, action) => {
      draftState.currentLayer = action.payload;
    })
    .addCase(setLayers, (draftState, action) => {
      draftState.layers = action.payload;
    });
});
